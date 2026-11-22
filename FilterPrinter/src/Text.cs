namespace FilterPrinterMod
{
    internal static class Text
    {
        internal static string Get(string key, params object[] args)
        {
            return ModHelper.GetLocalized(FilterPrinterMod.ModId, key, args);
        }
    }
}
