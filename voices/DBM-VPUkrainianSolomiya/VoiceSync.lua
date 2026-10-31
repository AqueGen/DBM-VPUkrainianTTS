-- Copyright (c) 2026 AqueGen. All rights reserved. See LICENSE.
-- Shared by every Ukrainian pack (identical copy in each folder); the first one loaded installs the hook.
if not DBM or DBM.UkrainianVoiceSync then return end
DBM.UkrainianVoiceSync = true

local PACKS = { UkrainianTTS = true, UkrainianAlex = true, UkrainianEvgeniy = true, UkrainianSolomiya = true }
local COUNT_OPTIONS = { "CountdownVoice", "CountdownVoice2", "CountdownVoice3", "PullVoice" }
local EVENT_OPTIONS = { "EventSoundVictory2", "EventSoundWipe", "EventSoundPullTimer", "EventSoundEngage2" }

-- DBM also calls CheckVoicePackVersion for every pack at login and 10 s later, so only a real change of
-- ChosenVoicePack2 may move anything; otherwise a mix the player set up (Polina warnings, Alex countdown) resets.
local lastChosen

-- Picking one of our packs in DBM moves every other option that pointed at one of our packs to the same voice.
hooksecurefunc(DBM, "CheckVoicePackVersion", function(self, value)
	local options = self.Options
	local previous = lastChosen or options.ChosenVoicePack2
	lastChosen = options.ChosenVoicePack2
	if value ~= options.ChosenVoicePack2 or value == previous or not PACKS[value] or not self.VoiceVersions[value] then return end
	local changed = false
	for _, key in ipairs(COUNT_OPTIONS) do
		local current = type(options[key]) == "string" and options[key]:match("^VP: (%w+)$")
		if current and PACKS[current] and current ~= value then
			options[key] = "VP: " .. value
			changed = true
		end
	end
	for _, key in ipairs(EVENT_OPTIONS) do
		local current = type(options[key]) == "string" and options[key]:match("^Interface\\AddOns\\DBM%-VP(%w+)\\events\\")
		if current and PACKS[current] and current ~= value then
			options[key] = options[key]:gsub("DBM%-VP%w+", "DBM-VP" .. value, 1)
			changed = true
		end
	end
	if changed then
		C_Timer.After(1, function() self:BuildVoiceCountdownCache() end) -- countdowns register a moment after the pack check at login
	end
end)
