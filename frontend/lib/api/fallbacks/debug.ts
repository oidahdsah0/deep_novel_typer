import type { DebugSnapshot, ModelQueueSnapshot } from "../types/index";

export const fallbackDebugSnapshot: DebugSnapshot = {
  token_usage: {
    today: 0,
    last_7_days: 0,
    last_30_days: 0,
    total: 0,
    unknown_usage_requests: 0,
  },
  request_logs: [],
};

export const fallbackModelQueueSnapshot: ModelQueueSnapshot = {
  worker_count: 0,
  queued_count: 0,
  running_count: 0,
  items: [],
};
