local _, ns = ...

local ACTION_TEXT = "DBM_VP_UKRAINIANTTS_ACTION_TEXT"
local FORMAT = "DBM_VP_UKRAINIANTTS_FORMAT"
local KEEP_BAR_NAMES = "DBM_VP_UKRAINIANTTS_KEEP_BAR_NAMES"

local DEMO_KEY = "aesoon"
local DEMO_SOUND = "Interface\\AddOns\\DBM-VPUkrainianTTS\\" .. DEMO_KEY .. ".ogg"

local FORMATS = {
	{"tagphrase", "Тег + фраза"},
	{"tag", "Тільки тег"},
	{"phrase", "Тільки фраза"},
}

local barSetting = {}

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
	if setting:GetVariable() == ACTION_TEXT and value and not ns.applied then
		ns.ApplyRenames()
		if ns.applied then return end
	end
	StaticPopup_Show("DBM_VP_UKRAINIANTTS_RELOAD")
end

local function OnBarNamesChanged(_, _, value)
	if DBM and DBM.Options then
		DBM.Options.ShortTimerText = not value
	end
end

local function Demo()
	PlaySoundFile(DEMO_SOUND, "Master")
	print("|cff308530DBM Voice Ukrainian|r: " .. (ns.TextFor(DEMO_KEY) or "?") .. " (1)")
end

local function Register()
	local db = ns.DB()
	barSetting.keepBarNames = not (DBM and DBM.Options and DBM.Options.ShortTimerText)

	local category, layout = Settings.RegisterVerticalLayoutCategory("DBM Voice Ukrainian")

	local actionText = Settings.RegisterAddOnSetting(category, ACTION_TEXT,
		"actionText", db, Settings.VarType.Boolean, "Текстові підказки", false)
	Settings.CreateCheckbox(category, actionText,
		"Замінює назву здібності в попередженнях DBM на дію тим самим текстом, який промовляє озвучка.")

	local format = Settings.RegisterAddOnSetting(category, FORMAT,
		"format", db, Settings.VarType.String, "Формат підказки", "tagphrase")
	Settings.CreateDropdown(category, format, function()
		local container = Settings.CreateControlTextContainer()
		for _, entry in ipairs(FORMATS) do
			container:Add(entry[1], entry[2])
		end
		return container:GetData()
	end, "Тег - коротке слово дії: АОЕ, ТАНК, ЗБИЙ, РОЗВІЙ, ПОГЛИНИ, АДДИ, ВІДІЙДИ, УХИЛЯЙСЯ, "
		.. "РОЗІЙДІТЬСЯ, ЗБЕРІТЬСЯ. Фраза - те, що каже озвучка.")

	local keepBarNames = Settings.RegisterAddOnSetting(category, KEEP_BAR_NAMES,
		"keepBarNames", barSetting, Settings.VarType.Boolean, "Не чіпати смуги таймерів", false)
	Settings.CreateCheckbox(category, keepBarNames,
		"Лишає назви здібностей на смугах таймерів. Це перемикач самого DBM "
		.. "(Timer Bars - Bar Behavior - Use spell renames on timer text), пак лише вимикає його за вас.")

	Settings.SetOnValueChangedCallback(ACTION_TEXT, OnChanged)
	Settings.SetOnValueChangedCallback(FORMAT, OnChanged)
	Settings.SetOnValueChangedCallback(KEEP_BAR_NAMES, OnBarNamesChanged)

	if layout then
		layout:AddInitializer(CreateSettingsButtonInitializer("", "Прослухати", Demo,
			"Програє приклад і друкує в чат, як виглядатиме підказка.", false))
	end

	Settings.RegisterAddOnCategory(category)
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:RegisterEvent("PLAYER_SPECIALIZATION_CHANGED")
frame:SetScript("OnEvent", function(_, event, arg)
	if event == "ADDON_LOADED" then
		if arg == "DBM-VPUkrainianTTS" then
			Register()
		end
	elseif arg == "player" and ns.applied and ns.appliedRole ~= ns.Role() then
		StaticPopup_Show("DBM_VP_UKRAINIANTTS_RELOAD")
	end
end)
