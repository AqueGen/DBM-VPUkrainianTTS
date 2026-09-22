local _, ns = ...

local defaults = {
	actionText = false,
	format = "tagphrase",
}

ns.PREFIX = "|cff308530DBM Voice Ukrainian|r: "
ns.L = {
	ON = "текстові підказки увімкнено.",
	OFF = "текстові підказки вимкнено.",
	RELOAD = "потрібне перезавантаження інтерфейсу: /reload",
	PENDING = "підказки застосуються, щойно завантажиться бойовий мод - на вході в підземелля чи рейд.",
	DBM_RENAMES_OFF = "у DBM вимкнено 'Use spell renames on announcement text' (Alerts - Special Announcements), "
		.. "без нього підказки не з'являться.",
	USAGE = "/uatext, /uatext on, /uatext off",
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
	for key, value in pairs(defaults) do
		if db[key] == nil then
			db[key] = value
		end
	end
	return db
end

function ns.Role()
	if not DBM or not DBM.IsTank then return "dps" end
	if DBM:IsTank() then return "tank" end
	if DBM:IsHealer() then return "healer" end
	return "dps"
end

function ns.TextFor(voiceKey)
	local tag, phrase
	local action = ns.actionByVoice[voiceKey]
	if action then
		tag, phrase = action[1], action[2]
		local byRole = action[3]
		if byRole then
			phrase = byRole[ns.Role()] or phrase
		end
	else
		phrase = ns.phraseByVoice[voiceKey]
		tag = ns.tagByVoice[voiceKey]
	end
	if not phrase then return nil end
	local format = ns.DB().format
	if not tag or format == "phrase" then
		return phrase
	elseif format == "tag" then
		return tag
	end
	return tag .. " | " .. phrase
end

function ns.TagList()
	local seen, tags = {}, {}
	for _, action in pairs(ns.actionByVoice) do
		if not seen[action[1]] then
			seen[action[1]] = true
			tags[#tags + 1] = action[1]
		end
	end
	for _, tag in pairs(ns.tagByVoice) do
		if not seen[tag] then
			seen[tag] = true
			tags[#tags + 1] = tag
		end
	end
	table.sort(tags)
	return tags
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
					ns.appliedRole = ns.appliedRole or ns.Role()
					local action = ns.actionByVoice[object.voiceFile]
					if action and action[3] then
						ns.appliedRoleVariants = true
					end
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
