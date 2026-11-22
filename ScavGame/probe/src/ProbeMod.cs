using UnityEngine;

namespace ScavProbe
{
    public sealed class ProbeMod : IMod
    {
        internal const string ModId = "harness.scav-probe";

        internal static bool Arrived;

        public void Init(ModManifest manifest)
        {
            Debug.Log("[ScavProbe] Init " + manifest.ID);
        }

        public void OnEnable()
        {
            ModHook.OnAfterhourArriveLate -= OnArrive;
            ModHook.OnAfterhourArriveLate += OnArrive;
            ModHook.OnAfterhourLeaveEarly -= OnLeave;
            ModHook.OnAfterhourLeaveEarly += OnLeave;
            ModHook.OnGameLoadedInit -= OnLoaded;
            ModHook.OnGameLoadedInit += OnLoaded;
            Debug.Log("[ScavProbe] enabled");
        }

        public void OnDisable()
        {
            ModHook.OnAfterhourArriveLate -= OnArrive;
            ModHook.OnAfterhourLeaveEarly -= OnLeave;
            ModHook.OnGameLoadedInit -= OnLoaded;
            Arrived = false;
            ProbeWindow.Close();
            Debug.Log("[ScavProbe] disabled");
        }

        private static void OnArrive(string locationId)
        {
            Arrived = locationId == "dumping_ground";
            Debug.Log("[ScavProbe] arrive " + locationId + " dumping=" + Arrived);
            if (Arrived)
            {
                ProbeWindow.Refresh("已到达垃圾场");
            }
        }

        private static void OnLeave(string locationId)
        {
            if (locationId == "dumping_ground")
            {
                Arrived = false;
                ProbeWindow.Close();
                Debug.Log("[ScavProbe] leave dumping_ground");
            }
        }

        private static void OnLoaded()
        {
            Arrived = false;
            ProbeWindow.Close();
            Debug.Log("[ScavProbe] game loaded, state reset");
        }
    }
}
