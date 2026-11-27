// read-only probe: log coordinator EUI64 and the NVM3 STACK_RESTORED_EUI64 token
const KEY = 0x10000 | 0xe12a;
class Eui64Probe {
    constructor(zigbee, mqtt, state, publishEntityState, eventBus, e1, e2, e3, settings, logger) { this.zigbee = zigbee; this.logger = logger; }
    async start() {
        const a = this.zigbee.zhController.adapter;
        await a.queue.execute(async () => {
            const eui = await a.ezsp.ezspGetEui64();
            const n = await a.ezsp.ezspGetTokenCount();
            let found = false;
            for (let i = 0; i < n; i++) {
                const [s, ti] = await a.ezsp.ezspGetTokenInfo(i);
                if (s === 0 && ti.nvm3Key === KEY) {
                    const [ds, td] = await a.ezsp.ezspGetTokenData(KEY, 0);
                    this.logger.info(`[eui64-probe] eui64=${eui} tokens=${n} restoredEui64 idx=${i} size=${ti.size} arr=${ti.arraySize} status=${ds} data=${td.data.toString("hex")}`);
                    found = true;
                }
            }
            if (!found) this.logger.info(`[eui64-probe] eui64=${eui} tokens=${n} restoredEui64 token NOT found`);
        });
    }
    async stop() {}
}
module.exports = Eui64Probe;
