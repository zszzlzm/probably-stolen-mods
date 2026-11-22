using UnityEngine;

namespace ScavArcade
{
    public sealed class ScavArcadeMod : IMod
    {
        internal const string ModId = "harness.scav-arcade";

        internal static bool Arrived;

        public void Init(ModManifest manifest)
        {
            Debug.Log("[ScavArcade] Init " + manifest.ID);
        }

        public void OnEnable()
        {
            ModHook.OnAfterhourArriveLate -= OnArrive;
            ModHook.OnAfterhourArriveLate += OnArrive;
            ModHook.OnAfterhourLeaveEarly -= OnLeave;
            ModHook.OnAfterhourLeaveEarly += OnLeave;
            ModHook.OnGameLoadedInit -= OnLoaded;
            ModHook.OnGameLoadedInit += OnLoaded;
            ModHook.OnLootRolled -= ArcadeWindow.OnLootRolled;
            ModHook.OnLootRolled += ArcadeWindow.OnLootRolled;
            Debug.Log("[ScavArcade] enabled");
        }

        public void OnDisable()
        {
            ModHook.OnAfterhourArriveLate -= OnArrive;
            ModHook.OnAfterhourLeaveEarly -= OnLeave;
            ModHook.OnGameLoadedInit -= OnLoaded;
            ModHook.OnLootRolled -= ArcadeWindow.OnLootRolled;
            Arrived = false;
            ArcadeWindow.Close();
            ArcadeWindow.ResetBoard();
            Debug.Log("[ScavArcade] disabled");
        }

        private static void OnArrive(string locationId)
        {
            Arrived = locationId == "dumping_ground";
            if (Arrived)
            {
                ArcadeWindow.OnArrive();
            }
            Debug.Log("[ScavArcade] arrive " + locationId + " dumping=" + Arrived);
        }

        private static void OnLeave(string locationId)
        {
            if (locationId == "dumping_ground")
            {
                Arrived = false;
                ArcadeWindow.Close();
                Debug.Log("[ScavArcade] leave dumping_ground");
            }
        }

        private static void OnLoaded()
        {
            Arrived = false;
            ArcadeWindow.Close();
            ArcadeWindow.ResetBoard();
            Debug.Log("[ScavArcade] game loaded");
        }
    }
}
