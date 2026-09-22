local _, ns = ...

local defaults = {
	actionText = false,
	showTags = true,
}

function ns.DB()
	DBMVPUkrainianTTSDB = DBMVPUkrainianTTSDB or {}
	for key, value in pairs(defaults) do
		if DBMVPUkrainianTTSDB[key] == nil then
			DBMVPUkrainianTTSDB[key] = value
		end
	end
	return DBMVPUkrainianTTSDB
end

function ns.TextFor(voiceKey)
	local tag, phrase
	local action = ns.actionByVoice[voiceKey]
	if action then
		tag, phrase = action[1], action[2]
	else
		phrase = ns.phraseByVoice[voiceKey]
		tag = ns.tagByVoice[voiceKey]
	end
	if not phrase then return nil end
	if tag and ns.DB().showTags then
		return tag .. " | " .. phrase
	end
	return phrase
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
