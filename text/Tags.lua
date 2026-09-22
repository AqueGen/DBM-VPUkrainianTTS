local _, ns = ...

local keysByTag = {
	["АОЕ"] = {
		"aesoon", "specialsoon", "breathsoon", "slamincoming", "pushbackincoming",
		"stompsoon", "stompstart", "quake", "shockwave", "lightstorm", "wwsoon",
		"whirlwind", "stilldanger", "takedamage", "healall", "healfull",
	},
	["ТАНК"] = {
		"defensive", "holdit", "tankcombo", "changemt", "swapsoon", "tauntboss",
		"dshigh", "sunderhigh", "tankheal",
	},
	["ЗБИЙ"] = {
		"kickcast", "helpkick", "kick1r", "kick2r", "kick3r", "kick4r", "kick5r",
		"interruptsoon", "kickorstopcast", "interruptbyeye", "stopcast", "trannow",
	},
	["РОЗВІЙ"] = {
		"dispelnow", "helpdispel", "dispelboss", "riftdispel",
	},
	["ПОГЛИНИ"] = {
		"helpsoak", "lightsoak", "voidsoak", "soakbeam", "soakincoming",
	},
	["АДДИ"] = {
		"mobsoon", "mobkill", "mobout", "killmob", "bigmob", "bigmobsoon", "killbigmob",
		"killmine", "killspirit", "ghostsoon", "engineercoming", "firecallercoming",
		"securityguardcoming", "slagelementalcoming", "targetchange", "changetarget",
		"attackblood", "attackbloodthirster", "attackcannon", "attackdeathcaller",
		"attackdoomfire", "attackfelblood", "attackflesheater", "attackhulkingterror",
		"attackmindfungus", "attacksporeshooter", "attacktotem", "attackturret",
		"attackshield", "attacktank", "attbomb",
	},
	["ВІДІЙДИ"] = {
		"scatter", "scattersoon", "runout", "runaway", "justrun", "lineapart", "farfromline",
		"bombyou", "bombrun", "bombsoon", "bombnow", "firerun", "laserrun", "meteorrun",
		"orbrun", "barrageonway", "focusedchaosyou", "wroughtchaosyou", "shadowrun",
		"watchstep", "watchfeet", "watchwave", "watchorb", "frontal", "frontalyou",
		"chargemove", "carefly", "iceorbmove", "rollincoming", "trapsincoming",
		"beamincoming", "gloomincoming", "orbsincoming", "runesincoming", "boundingcleave",
		"getknockedup", "movesoon", "keepmove", "cntnuemove", "kite",
	},
}

ns.tagByVoice = {}
for tag, keys in pairs(keysByTag) do
	for _, key in ipairs(keys) do
		ns.tagByVoice[key] = tag
	end
end
