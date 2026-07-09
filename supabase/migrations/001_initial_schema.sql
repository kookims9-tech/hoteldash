-- Phase 2 initial schema (reference only — not applied in Phase 1)
-- See docs/plan/05_ERD_Phase2_아키텍처.md

CREATE TABLE hotels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  room_count INT DEFAULT 150,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE revenue_daily (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
  business_date DATE NOT NULL,
  occupancy_pct NUMERIC(5,2),
  room_revenue NUMERIC(14,2) NOT NULL DEFAULT 0,
  spa_revenue NUMERIC(14,2) NOT NULL DEFAULT 0,
  fb_revenue NUMERIC(14,2) NOT NULL DEFAULT 0,
  total_revenue NUMERIC(14,2) NOT NULL DEFAULT 0,
  synced_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (hotel_id, business_date)
);

CREATE INDEX idx_revenue_daily_hotel_date ON revenue_daily (hotel_id, business_date DESC);

CREATE TABLE room_inspections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
  room_no TEXT NOT NULL,
  cleaner TEXT,
  clean_status TEXT,
  inspector TEXT,
  inspector_date DATE,
  result TEXT,
  repair_staff TEXT,
  repair_date DATE,
  note TEXT,
  synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_room_inspections_hotel ON room_inspections (hotel_id, inspector_date DESC);

CREATE TABLE voc_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
  review_date DATE,
  rating INT CHECK (rating BETWEEN 1 AND 5),
  channel TEXT,
  body TEXT,
  category TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE voc_complaint_summary (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  count INT NOT NULL DEFAULT 0,
  period_start DATE,
  period_end DATE
);

CREATE TABLE alert_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
  rule_id TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('critical', 'warning', 'info')),
  payload JSONB NOT NULL DEFAULT '{}',
  fired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  acknowledged BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE automation_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
  task_type TEXT NOT NULL,
  title TEXT NOT NULL,
  assignee TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  due_date DATE,
  source_refs JSONB DEFAULT '[]'
);

ALTER TABLE revenue_daily ENABLE ROW LEVEL SECURITY;
