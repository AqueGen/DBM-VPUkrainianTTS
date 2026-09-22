local _, ns = ...

local ACTION_TEXT = "DBM_VP_UKRAINIANTTS_ACTION_TEXT"
local FORMAT = "DBM_VP_UKRAINIANTTS_FORMAT"

local FORMATS = {
	{"tagphrase", "Тег + фраза"},
	{"tag", "Тільки тег"},
	{"phrase", "Тільки фраза"},
}

StaticPopupDialogs["DBM_VP_UKRAINIANTTS_RELOAD"] = {
	text = "Зміна набуде чинності після перезавантаження інтерфейсу.",
	button1 = "Перезавантажити",
	button2 = "Пізніше",
	OnAccept = ReloadUI,
	timeout = 0,
	whileDead = true,
	hideOnEscape = true,
}

local function OnChanged(_, setting, value)
	if setting:GetVariable() == ACTION_TEXT and value then
		ns.ApplyRenames()
		if not ns.applied then
			print(ns.PREFIX .. ns.L.PENDING)
		elseif not ns.WarningsShowRenames() then
			print(ns.PREFIX .. ns.L.DBM_RENAMES_OFF)
		end
	elseif ns.applied then
		StaticPopup_Show("DBM_VP_UKRAINIANTTS_RELOAD")
	end
end

local function Register()
	local db = ns.DB()
	local category = Settings.RegisterVerticalLayoutCategory("DBM Voice Ukrainian")

	local actionText = Settings.RegisterAddOnSetting(category, ACTION_TEXT, "actionText", db,
		Settings.VarType.Boolean, "Текстові підказки", false)
	Settings.CreateCheckbox(category, actionText,
		"Замінює назву здібності в попередженнях DBM на дію тим самим текстом, який промовляє озвучка: "
		.. "\"АОЕ | Скоро шкода по площі\" замість \"Rage of the Shackled\".")

	local format = Settings.RegisterAddOnSetting(category, FORMAT, "format", db,
		Settings.VarType.String, "Формат підказки", "tagphrase")
	Settings.CreateDropdown(category, format, function()
		local container = Settings.CreateControlTextContainer()
		for _, entry in ipairs(FORMATS) do
			container:Add(entry[1], entry[2])
		end
		return container:GetData()
	end, "Тег - коротке слово дії: АОЕ, ТАНК, ЗБИЙ, РОЗВІЙ, ПОГЛИНИ, АДДИ, ВІДІЙДИ, УХИЛЯЙСЯ, "
		.. "РОЗІЙДІТЬСЯ, ЗБЕРІТЬСЯ та інші. Фраза - те, що каже озвучка.")

	Settings.SetOnValueChangedCallback(ACTION_TEXT, OnChanged)
	Settings.SetOnValueChangedCallback(FORMAT, OnChanged)
	Settings.RegisterAddOnCategory(category)
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:SetScript("OnEvent", function(self, _, addon)
	if addon ~= "DBM-VPUkrainianTTS" then return end
	self:UnregisterAllEvents()
	Register()
end)
