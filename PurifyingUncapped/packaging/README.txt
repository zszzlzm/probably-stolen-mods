净化无上限  v1.0.0
============================================================

【这个模组做什么】
把「净化水质」基因的 每晚去除比例上限 95% 改成 100%。

原版公式是：
    share = min(0.95, 0.1 × 等级^0.75)

所以 21 级就到顶 95%，之后升到 26 级也只是把「纯度最高可达」从
99.99% 抬到 100.0%，去除速度一直是 95%。想提高吞吐只能多摆几台
水培机——更多实体、更卡、每晚更多点击。

装上本模组后：
    20 级   94.57%（不变）
    21 级   98.10%（tooltip 显示 98%）
    22-25   100%（tooltip 显示 100%）
    26 级   100%（一晚清掉除矿物质外的所有污染物）

【注意：重金属门槛没动】
净化比例和「纯度上限」是两套逻辑。重金属的 floor 是
    baseMaxPurityFromMachine / 等级
所以 22-25 级重金属仍会被卡在 0.01%，要到 26 级（floor 归零）
才会真正除矿物质外全清。本模组只拆 95% 上限，没有动这个门槛。

【安装】
1. 把整个 PurifyingUncapped-v1.0.0 文件夹放进：
       <游戏目录>/Mods/
   （Steam 版一般是 ...\steamapps\common\Probably Stolen\Mods\）
2. 启动游戏，打开「模组」菜单，找到「净化无上限」，点「审核并启用」
3. 启用后可能需要重启游戏一次（模组菜单会提示）

【兼容性 / 卸载】
· 只对 PlantWaterQuality.PurifyingShare(int) 打一个 Harmony Prefix，
  玩法和 tooltip 一起生效
· 不写存档、不新增物品/配方，卸载后直接恢复原版行为
· 与只改物品/配方的模组无冲突；不要和其它同样改 PurifyingShare 的
  模组同时装（后加载的会覆盖前面的 Prefix）

【验证是否生效】
· 看 22 级以上净化种子/DNA 磁盘的说明：
  「每晚去除各类污染物中的100%」
· Player.log 里应有：
      [ModLoader] Loading: PurifyingUncappedMod.dll
      [ModLoader]   Harmony: 1 method(s) patched

【反馈】
遇到问题请附上 Player.log（位于
%LOCALAPPDATA%Low\Questing Goose Studio\Probably Stolen\Player.log）
