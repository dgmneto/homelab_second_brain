// z2m external extension: remove bindings that still target the OLD coordinator IEEE after the
// 2026-11-24 SLZB-06M -> SLZB-MR5U migration (new coordinator has a different IEEE).
// Stale binds make devices broadcast NWK_addr_req for an address nobody owns -> broadcast storm,
// "Delivery of BROADCAST failed for '65533'" and failed unicasts (commands to switches time out).
// - rx-on devices are fixed at start; sleepy ones the moment they next talk (lastSeenChanged).
// - devices with no bind to the NEW coordinator get meta.configured cleared, so z2m's Configure
//   extension re-runs configure (binds + reporting) on their next message.
// Install: MQTT zigbee2mqtt/bridge/request/extension/save {"name":"cleanup-old-coordinator-binds.js","code":"..."}
// Remove when it logs "[old-binds] all clean" (bridge/request/extension/remove {"name":...}).
// 2026-11-27: swapped. The coordinator IEEE was restored to 0x8c8b…, so binds to the MR5U-native 0xfc11… are now the stale ones.
// Set OLD = the IEEE devices must NOT be bound to, NEW = the current coordinator IEEE.
const OLD = "0xfc1119fffeaa036b";
const NEW = "0x8c8b48fffe9583ba";

class CleanupOldCoordinatorBinds {
    constructor(zigbee, mqtt, state, publishEntityState, eventBus, enableDisableExtension, restartCallback, addExtension, settings, logger) {
        this.zigbee = zigbee;
        this.eventBus = eventBus;
        this.logger = logger;
        this.busy = new Set();
        this.lastTry = new Map();
        this.lastCount = -1;
    }

    stale(dev) {
        const out = [];
        for (const ep of dev.zh.endpoints) {
            for (const b of ep._binds) {
                if (b.type === "endpoint" && b.deviceIeeeAddress === OLD) out.push([ep, b]);
            }
        }
        return out;
    }

    async fix(dev, why) {
        const name = dev.name;
        if (this.busy.has(name)) return;
        const st = this.stale(dev);
        if (!st.length) return;
        const now = Date.now();
        if (now - (this.lastTry.get(name) || 0) < 120000) return; // 2 min between attempts per device
        this.lastTry.set(name, now);
        this.busy.add(name);
        try {
            const hasNew = dev.zh.endpoints.some((ep) => ep._binds.some((b) => b.deviceIeeeAddress === NEW));
            if (!hasNew && dev.zh.meta && dev.zh.meta.configured !== undefined) {
                delete dev.zh.meta.configured;
                dev.zh.save();
                this.logger.info(`[old-binds] ${name}: no bind to new coordinator, cleared meta.configured (z2m will reconfigure)`);
            }
            for (const [ep, b] of st) {
                const fake = Object.create(Object.getPrototypeOf(ep));
                fake.deviceIeeeAddress = OLD;
                fake.ID = b.endpointID;
                try {
                    await ep.unbind(b.cluster, fake, true);
                    const i = ep._binds.indexOf(b);
                    if (i >= 0) {
                        ep._binds.splice(i, 1);
                        ep.save();
                    }
                    this.logger.info(`[old-binds] ${name}/${ep.ID} cluster ${b.cluster}: old coordinator bind removed (${why})`);
                } catch (e) {
                    this.logger.warning(`[old-binds] ${name}/${ep.ID} cluster ${b.cluster}: ${e.message} (${why}, will retry)`);
                    break; // device asleep/unreachable: retry on its next message
                }
            }
            this.report();
        } finally {
            this.busy.delete(name);
        }
    }

    report() {
        const left = [];
        for (const dev of this.zigbee.devicesIterator((d) => d.type !== "Coordinator")) {
            if (this.stale(dev).length) left.push(dev.name);
        }
        if (left.length === this.lastCount) return; // log only when it changes
        this.lastCount = left.length;
        this.logger.info(left.length ? `[old-binds] still stale (${left.length}): ${left.join(", ")}` : "[old-binds] all clean");
    }

    async start() {
        this.eventBus.onLastSeenChanged(this, (data) => {
            this.fix(data.device, "woke").catch((e) => this.logger.warning(`[old-binds] ${e.message}`));
        });
        this.report();
        (async () => {
            for (const dev of this.zigbee.devicesIterator((d) => d.type !== "Coordinator")) {
                if (dev.zh.type === "Router" || dev.zh.type === "EndDevice") {
                    await this.fix(dev, "start").catch((e) => this.logger.warning(`[old-binds] ${e.message}`));
                }
            }
        })();
    }

    async stop() {
        this.eventBus.removeListeners(this);
    }
}

module.exports = CleanupOldCoordinatorBinds;
