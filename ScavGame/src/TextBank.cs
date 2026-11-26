namespace ScavArcade
{
    internal static class TextBank
    {
        internal static string Get(string key, params object[] args)
        {
            return ModHelper.GetLocalized(ScavArcadeMod.ModId, "scavarcade." + key, args);
        }
    }
}
