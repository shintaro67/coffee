export type Bean = {
  id: number;
  name: string;
  roaster: string;
  process: string;
  roast_level: string;
  roast_date: string;
  is_archived: boolean;
  days_from_roast?: number;
};

export type BrewLog = {
  id: number;
  bean_id: number;
  bean_name?: string;
  date: string;
  days_from_roast: number;
  elapsed_time_total: number;
  max_weight: number;
  powder_weight: number;
  extract_weight: number;
  tds: number;
  yield_ey: number;
  brew_ratio: number;
  grind_size: string;
  dripper: string;
  acidity: number;
  sweetness: number;
  body: number;
  rating: number;
  notes: string;
  timeseries_json?: Array<{
    elapsed: number;
    weight: number;
    temp_kettle: number;
    temp_dripper: number;
    flow_rate: number;
  }>;
};

export type TelemetryPoint = {
  elapsed: number;
  weight: number;
  temp_kettle: number;
  temp_dripper: number;
  raw_flow_rate: number;
  received_at: number;
  sender_ip?: string;
};

export type BrewSessionSummary = {
  active: boolean;
  completed: boolean;
  bean_id: number | null;
  bean_name: string | null;
  powder_weight: number;
  target_ratio: number;
  target_water: number;
  elapsed: number;
  weight: number;
  progress: number;
  flow_rate: number;
  current_state: "idle" | "waiting" | "brewing" | "finished";
  timeseries_length: number;
};

export type TelemetryPacket = {
  type: "telemetry" | "session" | "ack" | "error";
  telemetry?: TelemetryPoint;
  session?: BrewSessionSummary;
  command?: "tare" | "start";
  message?: string;
};
