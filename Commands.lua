local _, ns = ...

local PREFIX = "|cff308530DBM Voice Ukrainian|r: "

SLASH_DBMVPUKRAINIANTTS1 = "/uatext"
SlashCmdList["DBMVPUKRAINIANTTS"] = function(input)
	local db = ns.DB()
	local argument = string.lower(string.match(input or "", "^%s*(%S*)") or "")
	if argument == "on" then
		db.actionText = true
	elseif argument == "off" then
		db.actionText = false
	elseif argument == "" then
		db.actionText = not db.actionText
	else
		print(PREFIX .. "/uatext, /uatext on, /uatext off")
		return
	end

	if db.actionText then
		if not ns.applied then
			ns.ApplyRenames()
		end
		print(PREFIX .. "текстові підказки увімкнено.")
		if not ns.applied then
			print(PREFIX .. "потрібне перезавантаження інтерфейсу: /reload")
		end
	else
		print(PREFIX .. "текстові підказки вимкнено, потрібне перезавантаження інтерфейсу: /reload")
	end
end
