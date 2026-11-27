using System.Globalization;

namespace LuxuryNomoreInjectorMod
{
    /// <summary>
    /// Balance numbers in one place.
    ///
    /// The vanilla factory <c>MedsItemDirectory.Injector</c> sets <c>unitValue = 50</c>; 1.0.x repriced every
    /// injector to a flat 350, which is a 7x markup. Players asked for 2-4x and for a knob, so the markup is
    /// now a multiplier over whatever the factory set, with 4x as the default (200) and 1x (50, i.e. no
    /// markup) available for anyone who only wants the LUXURY_ITEM tag.
    ///
    /// The setting is a **dropdown of the ten gears**, not a slider: the game renders a ranged number as a bare
    /// slider (ModConfigWindow.cs:103-107) with no readout, and the label is built only when the window opens,
    /// so a slider would not show which gear is selected. A string entry with Choices gets
    /// <c>AddDropdown</c>, which always displays the current option.
    ///
    /// The multiplier is read at item-creation time, so changing it affects newly created injectors only;
    /// items already sitting in a save keep the value they were created with.
    /// </summary>
    internal static class Balance
    {
        internal const string ConfigKey = "value_multiplier";
        internal const string ConfigSection = "Luxury Nomore Injector";

        internal const int DefaultMultiplier = 4;
        internal const int MinMultiplier = 1;
        internal const int MaxMultiplier = 10;

        /// <summary>Fallback base value if the factory ever stops setting one (it sets 50 in 0.46D).</summary>
        internal const long FallbackBaseValue = 50L;

        /// <summary>"1" .. "10" — one dropdown row per gear.</summary>
        internal static readonly string[] Choices = BuildChoices();

        private static string[] BuildChoices()
        {
            string[] choices = new string[MaxMultiplier - MinMultiplier + 1];
            for (int i = 0; i < choices.Length; i++)
            {
                choices[i] = (MinMultiplier + i).ToString(CultureInfo.InvariantCulture);
            }
            return choices;
        }
    }
}
