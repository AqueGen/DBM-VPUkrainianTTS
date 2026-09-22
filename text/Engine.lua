local _, ns = ...

ns.PREFIX = "|cff308530DBM Voice Ukrainian|r: "
ns.L = {
	PENDING = "підказки застосуються, щойно завантажиться бойовий мод - на вході в підземелля чи рейд.",
	DBM_RENAMES_OFF = "у DBM вимкнено 'Use spell renames on announcement text' (Alerts - Special Announcements), "
		.. "без нього підказки не з'являться.",
}

function ns.DB()
	DBMVPUkrainianTTSDB = DBMVPUkrainianTTSDB or {}
	if DBMVPUkrainianTTSDB.actionText == nil then
		DBMVPUkrainianTTSDB.actionText = false
	end
	return DBMVPUkrainianTTSDB
end

function ns.TextFor(voiceKey)
	local action = ns.actionByVoice[voiceKey]
	if action then
		return action[1] .. " | " .. action[2]
	end
	return ns.phraseByVoice[voiceKey]
end

function ns.WarningsShowRenames()
	if DBM and DBM.Options then
		return DBM.Options.SpecialWarningShortText and true or false
	end
	return true
end

function ns.ApplyRenames()
	if not ns.DB().actionText then return end
	if not DBM or not DBM.Mods or not DBM.AddRename then return end
	for _, mod in ipairs(DBM.Mods) do
		if mod.specwarns then
			for _, object in ipairs(mod.specwarns) do
				local text = object.voiceFile and ns.TextFor(object.voiceFile)
				if text and type(object.spellId) == "number" then
					DBM:AddRename(object.spellId, text)
					ns.applied = true
				end
			end
		end
	end
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:RegisterEvent("PLAYER_LOGIN")
frame:SetScript("OnEvent", function(_, event, addon)
	if event == "PLAYER_LOGIN" or (type(addon) == "string" and addon:find("^DBM")) then
		ns.ApplyRenames()
	end
end)
