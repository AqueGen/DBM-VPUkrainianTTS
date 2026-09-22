local _, ns = ...

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
		print(ns.PREFIX .. ns.L.USAGE)
		return
	end

	if db.actionText then
		ns.ApplyRenames()
		print(ns.PREFIX .. ns.L.ON)
		if not ns.applied then
			print(ns.PREFIX .. ns.L.PENDING)
		elseif not ns.WarningsShowRenames() then
			print(ns.PREFIX .. ns.L.DBM_RENAMES_OFF)
		end
	else
		print(ns.PREFIX .. ns.L.OFF)
		if ns.applied then
			print(ns.PREFIX .. ns.L.RELOAD)
		end
	end
end
