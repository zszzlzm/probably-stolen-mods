using UnityEngine;

namespace ScavArcade
{
    internal sealed class ArcadePulse : MonoBehaviour
    {
        private void Update()
        {
            ArcadeWindow.AutoTestTick();
            ArcadeWindow.Tick();
        }
    }
}
