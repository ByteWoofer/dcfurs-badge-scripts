# DC26 Defcon Furs badge (All file references are dc26-fur-scripts unless otherwise mentioned in this section)

## ABSTRACT
The following functionality can be triggered in the DCFurs26 badge over bluetooth with the default bluetooth firmware:
- display and retransmit an AWOO packet
- display a random emote
- display a specific emote
- clear rabies from the device

AWOO: This is recieved by "rx:AWOO" over serial to `main.py`
EMOTE: This is recieved by "rx:EMOTE" over serial to `main.py`

The format is: "rx:<name>=<argument>"
Argument is optional, can be used with "emote" E.G: "rx:emote=UwU" has no function with AWOO



## METHODOLOGY
This information was obtained by reading through the publically available source code for both the micropython software and the bluetooth chip's custom firmware. Below we have a walkthrough of how each of such things occurs in a near line by line fashion.

-------

Next step in learning is to identify what broadcasts the badge grabs and which it ignores. (OFF TO THE BLUETOOTH FIRMWARE!)
(These code snippits come from https://github.com/defconfurs/dc26-fur-scripts/blob/master/firmware/bluetooth/main.c )

Existing magic bytes in firmware:

		#define DC26_MAGIC_NONE		0x00
		#define DC26_MAGIC_RABIES	0x35
		#define DC26_MAGIC_AWOO 	0xa0
		#define DC26_MAGIC_EMOTE	0xb2
		#define DC26_MAGIC_VACCINE	0xce
		#define DC26_APPEARANCE		0x26dc
		#define DC26_MFGID_DCFURS	0x71ff

`DC26_APPEARANCE` is used to filter beacons that are "Not part of the game", To interact with the DC26 badge you'll need a `DC26_APPEARANCE` (0x26dc)

Bluetooth beacons for these badges utilize this data structure:

		struct dc26_scan_data {
			char name[32];
			uint16_t appearance;
			uint16_t mfgid;
			uint16_t serial;
			uint8_t magic;
			uint8_t length;
			uint8_t payload[16];
		};

Emotes are read over the air based initially on `DC26_APPEARANCE` for filtering, followed by magic byte for parsing. If you have the `DC26_MAGIC_EMOTE` this code section occurs:

(Here the object `data` contains the struct `dc26_scan_data` above extracted from a beacon)

		if ((data.magic == DC26_MAGIC_EMOTE) && dc26_emote_test_cooldowns(rssi)) {
				/* Emote selection... */
				if (data.length < 2) {
					printk("rx: mfgid=0x%02x emote=random\n", data.mfgid);
				}
				else {
					char emhex[sizeof(data.payload)*2 + 1] = {'\0'};
					for (int i = 0; (i < sizeof(data.payload)) && i < data.length; i++) {
						sprintf(&emhex[i*2], "%02x", data.payload[i]);
					}
					printk("rx: mfgid=0x%02x rssi=%d emote=%s\n", data.mfgid, rssi, emhex);
				}
		}

Here we can see two pathways for parsing to take, yielding a random emote or a targeted emote: 

	printk("rx: mfgid=0x%02x emote=random\n", data.mfgid);

or
	printk("rx: mfgid=0x%02x rssi=%d emote=%s\n", data.mfgid, rssi, emhex);
	
(printk is used to send data to python over the serial port, hence the readline() in line 42 of https://github.com/defconfurs/dc26-fur-scripts/blob/master/main.py )


So after being transmitted to main.py `"rx: mfgid=0x%02x emote=random\n"` would be split by line 46 into the objects `event` and `x` being `"rx"` and `" mfgid=0x%02x emote=random\n"` respectively. From there `x` would be rstripped and further split by line 47 into the object args being `['mfgid=0x%02x', 'emote=random']`. This arg list would then be passed to line 14's `blerx` function which would iterate over them, separating <name>=<argument> pairs, looking for 'emote' or 'awoo' within the name field.

 > this means if a beacon was sent using the format dc26_scan_data with an appearance of `DC26_APPEARANCE` and a magic of `DC26_MAGIC_EMOTE` it should EMOTE. 

(Scratch this idea ->) ~~Also since we control data.length and data.length is the end contition for the data.payload read operation we may be able to read past the end of the allocated buffer for emhex)((Nix this idea, they explicitly check against this with a pair of validations `"(i < sizeof(data.payload)) && i < data.length;"` Cute idea though))~~

---

parsing of AWOO happens in a similar fashion to that of EMOTE. After filtering based on `DC26_APPEARANCE` they are parsed using this code here:

		if ((data.magic == DC26_MAGIC_AWOO) && (data.mfgid == DC26_MFGID_DCFURS) && (dc26_awoo_cooldown < k_uptime_get()) && (data.length >= 3)) {
				/* Awoo beacon */
				uint8_t ttl = data.payload[0];
				uint16_t origin = (data.payload[2] << 8) | data.payload[1];
				printk("rx: awoo origin=0x%04x\n", origin);

				/* Route the magic beacon another hop */
				dc26_awoo_cooldown = k_uptime_get() + K_SECONDS(300);
				dc26_start_awoo(ttl, origin);
		}

Here we see a check of magic byte, that the manufacturer's ID is `DC26_MFGID_DCFURS` (0x71ff) and `dc26_awoo_cooldown` (Defaultly 0 then incremented to be current time + 300 seconds after transmitting an awoo) is less than `k_uptime_get()` (Current time) and the `data.length` is 3 bytes or greater (required for the upcoming data extraction) we parse the data to rebroadcast. a `uint8_1 ttl` object is created with `data.payload[0]` (holding what I can only imagine to be a time to live), and a `uint16_t origin` object is created holding a 2 byte identifier for the originator of said awoo. (Populated by bitshifting `data.payload[2]` 8 bits left then ORing it together with `data.payload[1]`. From here the command is sent up the serial port as `printk("rx: awoo origin=0x%04x\n", origin);` which I will follow after finishing out the execution in the firmware. The cooldown `dc26_awoo_cooldown` is then updated with the current time plus 300 seconds and `dc26_start_awoo(ttl, origin)` is called. 

`dc26_start_awoo` contains the following code:

		/* Start generating an Awoo beacon */
		static void dc26_start_awoo(uint8_t ttl, uint16_t origin)
		{
			if (!ttl) {
				return;
			}

			const struct bt_le_adv_param awoo_param = {
				.options = 0,
				.interval_min = BT_GAP_ADV_FAST_INT_MIN_2,
				.interval_max = BT_GAP_ADV_FAST_INT_MAX_2,
			};

			/* Awoo beacons */
			u8_t awoo_data[] = {
				(DC26_MFGID_DCFURS >> 0) & 0xff,
				(DC26_MFGID_DCFURS >> 8) & 0xff,
				DC26_MAGIC_AWOO,		/* Magic */
				(dc26_badge_serial >> 0) & 0xff, /* Serial */
				(dc26_badge_serial >> 8) & 0xff,
				ttl - 1,				/* TTL */
				(origin >> 0) & 0xff,	/* Origin */
				(origin >> 8) & 0xff,
			};
			struct bt_data awoo[] = {
				BT_DATA_BYTES(BT_DATA_GAP_APPEARANCE, (DC26_APPEARANCE & 0x00ff) >> 0, (DC26_APPEARANCE & 0xff00) >> 8),
				BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
				BT_DATA_BYTES(BT_DATA_NAME_COMPLETE, 'D', 'E', 'F', 'C', 'O', 'N', 'F', 'u', 'r', 's'),
				BT_DATA(BT_DATA_MANUFACTURER_DATA, awoo_data, sizeof(awoo_data))
			};

			bt_le_adv_stop();
			bt_le_adv_start(&awoo_param, awoo, ARRAY_SIZE(awoo), NULL, 0);
			k_timer_start(&dc26_magic_timer, K_SECONDS(5), 0);
		}

To begin `ttl` is checked not to equal zero (under threat of premature return) then a `awoo_param` object is populated with `options`, `interval_min` and `interval_max` (I suspect this structure is core to the operation of the bluetooth module as their definitions occur outside `main.c` and are not utilized within the file). Next an array of unsigned 8 bit values `awoo_data` is created, holding the upper and lower portion of `DC26_MFGID_DCFURS`, `DC26_MAGIC_AWOO`, upper and lower of `dc26_badge_serial`, the `ttl`, and upper and lower of the `origin`. Then an array of `bt_data awoo` is created, holding three `BT_DATA_BYTES` objects and one `BT_DATA` object. the `DC26_APPEARANCE`, Some bluetooth flags defined outside the file (And as such most likely core to the base firmware), the device's complete name, hardcoded to "DEFCONFurs" and the prior `awoo_data` array. `bt_le_adv_stop();` and `bt_le_adv_start(&awoo_param, awoo, ARRAY_SIZE(awoo), NULL, 0);` are then called sequentially (which I can only assume to mean broadcasting halts and restarts using the broadcast parameters in `awoo_param`, sending the `bt_data awoo` structure) then `k_timer_start(&dc26_magic_timer, K_SECONDS(5), 0);` is called which I can only assume causes it to broadcast said AWOO for 5 seconds before returning to normal operation.

---

Back within the python side however, `main.py` catches `printk("rx: awoo origin=0x%04x\n", origin);` on line 42 which should roughly parse to something like `"rx: awoo origin=0xFFFF\n"`. Here the reaction is the same as with emote. The string is split on the colon, arguments are trimmed of the newline then split from the right side of the colon into a list delimited by space, that list is passed to `blerx` on line 14 and arguments are iterated over till 'awoo' is seen. At this point `msg` is set equal to `animations.scroll(" AWOOOOOOOOOOOOOO")`, `delay` is set to zero `msg.draw()` displays the awoo frame (based on `__init__.py` in the animations folder) and `pyb.delay(msg.interval)` extracts the 250 ms interval from `animations/scroll.py` line 72 and waits on it. After the wait the interval is added to `delay` and this repeats till `delay` has accumulated more than 5 seconds of displaying.

>This means that as long as the beacon read is formatted like dc26_scan_data with appearance equal to DC26_APPEARANCE, a magic of DC26_MAGIC_EMOTE, the manufacturer's ID is DC26_MFGID_DCFURS (0x71ff), a payload containing a 1 byte ttl greater than zero and a 2 byte origin exists and the local value dc26_awoo_cooldown is 300 seconds greater than the local time pulled from k_uptime_get() an awoo should be triggered and the cooldown updated to wait another 300 seconds.

### CONCLUSIONS:
So far it has been discovered that the bluetooth firmware appears to handle filtering beacons using a hex string `DC26_APPEARANCE` which should be within the beacon. If that is true a list of magic bytes is checked against for the function that should occur. These functions appear to include causing/continuing a howl(`DC26_MAGIC_AWOO`) displaying an emote(`DC26_MAGIC_EMOTE`), or clearing the device of rabies(`DC26_MAGIC_VACCINE`). 

### Further Research:
I have yet to determine how rabies is transmitted to the device, the only mention of the rabies magic byte (`DC26_MAGIC_RABIES`) is within `static void dc26_beacon_reset(void)` where it appears to change the default broadcast magic byte from none (`DC26_MAGIC_NONE`) to the formentioned rabies byte, `dc26_is_rabid()` which simply replies with a boolean based on `NRF_UICR->CUSTOMER[0]` (Which must be the rabies flag on chip) and `dc26_cure_rabies()` which simply sets that byte back to zero. At no point have I found something in the firmware that would change said byte to 1 yet it appears to have existed during the convention as shown by hamster's [video](https://www.youtube.com/watch?v=j_Qz_1RU4U4)


[GermaniumSystem](https://gist.github.com/GermaniumSystem/) also has some information about this badge as well including:   
[Custom Firmware](https://gist.github.com/GermaniumSystem/3db6e8c266bb1857db46e126722399af#file-about-txt)   
[beacon broadcast diagram](https://gist.github.com/GermaniumSystem/d785ab9717dda672419740a40b0623bb)   
[beacon broadcast script](https://gist.github.com/GermaniumSystem/f13153c91b3ca0924aeffbe7893fdca7)   
