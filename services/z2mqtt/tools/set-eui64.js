// One-shot: write NVM3 STACK_RESTORED_EUI64 so the SLZB-MR5U answers as the old coordinator IEEE
// 0x8c8b48fffe9583ba (all pre-migration bindings / TC address point to it). Takes effect on next NCP reset.
// Revert: same with data ffffffffffffffff. Remove this extension after use.
const KEY = 0x10000 | 0xe12a;
const DATA = "ba8395feff488b8c"; // little-endian of 0x8c8b48fffe9583ba
class SetEui64 {
    constructor(zigbee, mqtt, state, publishEntityState, eventBus, e1, e2, e3, settings, logger) { this.zigbee = zigbee; this.logger = logger; }
    async start() {
        const a = this.zigbee.zhController.adapter;
        await a.queue.execute(async () => {
            const [s0, cur] = await a.ezsp.ezspGetTokenData(KEY, 0);
            this.logger.info(`[set-eui64] before: status=${s0} data=${cur.data.toString("hex")}`);
            if (cur.data.toString("hex") !== DATA) {
                const st = await a.ezsp.ezspSetTokenData(KEY, 0, { data: Buffer.from(DATA, "hex"), size: 8 });
                this.logger.info(`[set-eui64] set status=${st}`);
            }
            const [s1, after] = await a.ezsp.ezspGetTokenData(KEY, 0);
            this.logger.info(`[set-eui64] after: status=${s1} data=${after.data.toString("hex")} (active after NCP reset)`);
        });
    }
    async stop() {}
}
module.exports = SetEui64;
