local _, ns = ...

ns.PREFIX = "|cff308530DBM Voice Ukrainian|r: "
ns.L = {
	PENDING = "підказки застосуються, щойно завантажиться бойовий мод - на вході в підземелля чи рейд.",
	DBM_RENAMES_OFF = "у DBM вимкнено 'Use spell renames on announcement text' (Alerts - Special Announcements), "
		.. "без нього підказки не з'являться.",
}

function ns.DB()
	DBMVPUkrainianTTSDB = DBMVPUkrainianTTSDB or {}
	local db = DBMVPUkrainianTTSDB
	if db.showTags ~= nil then
		if db.format == nil then
			db.format = db.showTags and "tagphrase" or "phrase"
		end
		db.showTags = nil
	end
	if db.actionText == nil then
		db.actionText = false
	end
	if db.format == nil then
		db.format = "tagphrase"
	end
	return db
end

function ns.TextFor(voiceKey)
	local action = ns.actionByVoice[voiceKey]
	local phrase = action and action[2] or ns.phraseByVoice[voiceKey]
	if not phrase then return nil end
	local tag = action and action[1]
	local format = ns.DB().format
	if not tag or format == "phrase" then
		return phrase
	elseif format == "tag" then
		return tag
	end
	return tag .. " | " .. phrase
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
