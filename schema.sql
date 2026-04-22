-- ============================================================
-- Duka ERP — Supabase SQL Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- Enable UUID generation
create extension if not exists "pgcrypto";


-- ============================================================
-- 1. SUPPLIERS
-- ============================================================
create table if not exists suppliers (
    supplier_id   uuid primary key default gen_random_uuid(),
    name          text not null,
    phone         text,
    created_at    timestamptz not null default now()
);


-- ============================================================
-- 2. CATALOG  (products / materials)
-- ============================================================
create table if not exists catalog (
    item_id               uuid primary key default gen_random_uuid(),
    name                  text not null,
    type                  text not null check (type in ('Material','Product','Service')),
    uom                   text not null check (uom  in ('Meters','Pieces','Flat Rate')),
    current_landed_cost   numeric(12,2) not null default 0,
    default_sell_price    numeric(12,2) not null default 0,
    is_active             boolean not null default true,
    created_at            timestamptz not null default now()
);


-- ============================================================
-- 3. INVENTORY LEDGER  (every stock movement)
-- ============================================================
create table if not exists inventory_ledger (
    ledger_id        uuid primary key default gen_random_uuid(),
    item_id          uuid not null references catalog(item_id),
    transaction_type text not null check (
        transaction_type in ('INWARD','SALE','ADJUSTMENT','VOID_SALE','OPENING_BALANCE')
    ),
    quantity_change  numeric(12,3) not null,   -- positive = stock in, negative = stock out
    unit_cost        numeric(12,2) default 0,
    reference_id     uuid,                      -- links to order_id when type = SALE / VOID_SALE
    notes            text,
    created_by       text,
    created_at       timestamptz not null default now()
);

create index if not exists idx_ledger_item_id on inventory_ledger(item_id);


-- ============================================================
-- 4. SALES ORDERS
-- ============================================================
create table if not exists sales_orders (
    order_id        uuid primary key default gen_random_uuid(),
    customer_name   text not null,
    customer_phone  text,
    total_amount    numeric(12,2) not null default 0,
    deposit_paid    numeric(12,2) not null default 0,
    balance_due     numeric(12,2) generated always as (total_amount - deposit_paid) stored,
    status          text not null default 'Pending' check (
        status in ('Pending','Ready','Delivered','Cancelled')
    ),
    notes           text,
    created_by      text,
    created_at      timestamptz not null default now()
);

create index if not exists idx_orders_status     on sales_orders(status);
create index if not exists idx_orders_created_at on sales_orders(created_at desc);


-- ============================================================
-- 5. ORDER LINES
-- ============================================================
create table if not exists order_lines (
    line_id      uuid primary key default gen_random_uuid(),
    order_id     uuid not null references sales_orders(order_id) on delete cascade,
    item_id      uuid not null references catalog(item_id),
    quantity     numeric(12,3) not null,
    unit_price   numeric(12,2) not null,
    line_cogs    numeric(12,2) not null default 0,
    is_voided    boolean not null default false,
    void_reason  text,
    voided_by    text,
    created_at   timestamptz not null default now()
);

create index if not exists idx_lines_order_id on order_lines(order_id);


-- ============================================================
-- 6. PURCHASE INVOICES  (stock inward records)
-- ============================================================
create table if not exists purchase_invoices (
    invoice_id      uuid primary key default gen_random_uuid(),
    item_id         uuid references catalog(item_id),
    supplier_id     uuid references suppliers(supplier_id),
    quantity        numeric(12,3) not null default 1,
    purchase_price  numeric(12,2) not null default 0,
    freight_cost    numeric(12,2) not null default 0,
    -- landed_cost = (purchase + freight) / qty, computed automatically
    landed_cost     numeric(12,4) generated always as (
        (purchase_price + freight_cost) / nullif(quantity, 0)
    ) stored,
    status          text not null default 'On Credit' check (status in ('On Credit','Paid')),
    is_voided       boolean not null default false,
    created_by      text,
    invoice_date    timestamptz not null default now()
);

create index if not exists idx_invoices_status on purchase_invoices(status);


-- ============================================================
-- 7. EXPENSES
-- ============================================================
create table if not exists expenses (
    expense_id   uuid primary key default gen_random_uuid(),
    description  text not null,
    amount       numeric(12,2) not null check (amount >= 0),
    category     text not null check (
        category in ('Electricity','Transport','Rent','Salaries','Supplies','Other')
    ),
    is_voided    boolean not null default false,
    created_by   text,
    expense_date date not null default current_date,
    created_at   timestamptz not null default now()
);


-- ============================================================
-- 8. AUDIT LOG  (append-only — no updates or deletes allowed)
-- ============================================================
create table if not exists audit_log (
    log_id                uuid primary key default gen_random_uuid(),
    table_name            text not null,
    record_id             text not null,
    action                text not null check (
        action in ('INSERT','UPDATE','VOID','ADJUST','DELETE')
    ),
    old_data              text,           -- JSON string of previous values
    new_data              text,           -- JSON string of new values
    changed_fields        text[],         -- array of field names that changed
    reason                text,
    performed_by_username text,
    performed_by_name     text,
    performed_at          timestamptz not null default now()
);

create index if not exists idx_audit_table_name  on audit_log(table_name);
create index if not exists idx_audit_performed_at on audit_log(performed_at desc);


-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Enable RLS on all tables
alter table suppliers         enable row level security;
alter table catalog           enable row level security;
alter table inventory_ledger  enable row level security;
alter table sales_orders      enable row level security;
alter table order_lines       enable row level security;
alter table purchase_invoices enable row level security;
alter table expenses          enable row level security;
alter table audit_log         enable row level security;

-- The app uses the service_role key (from secrets.toml SUPABASE_KEY),
-- which bypasses RLS automatically. These policies protect against
-- accidental anon/authenticated client access and enforce audit
-- log immutability even for service_role via a trigger (see below).

-- Allow full access via service_role (the key used in secrets.toml)
create policy "service_role full access" on suppliers
    for all to service_role using (true) with check (true);

create policy "service_role full access" on catalog
    for all to service_role using (true) with check (true);

create policy "service_role full access" on inventory_ledger
    for all to service_role using (true) with check (true);

create policy "service_role full access" on sales_orders
    for all to service_role using (true) with check (true);

create policy "service_role full access" on order_lines
    for all to service_role using (true) with check (true);

create policy "service_role full access" on purchase_invoices
    for all to service_role using (true) with check (true);

create policy "service_role full access" on expenses
    for all to service_role using (true) with check (true);

-- Audit log: SELECT + INSERT only (no UPDATE, no DELETE) for service_role
create policy "audit log select" on audit_log
    for select to service_role using (true);

create policy "audit log insert" on audit_log
    for insert to service_role with check (true);

-- Block UPDATE and DELETE on audit_log via a trigger (belt-and-suspenders)
create or replace function audit_log_immutable()
returns trigger language plpgsql as $$
begin
    raise exception 'audit_log is append-only: UPDATE and DELETE are not permitted';
end;
$$;

create or replace trigger trg_audit_no_update
    before update on audit_log
    for each row execute function audit_log_immutable();

create or replace trigger trg_audit_no_delete
    before delete on audit_log
    for each row execute function audit_log_immutable();


-- ============================================================
-- GENERATED balance_due NOTE
-- ============================================================
-- balance_due on sales_orders is a GENERATED ALWAYS column:
--   balance_due = total_amount - deposit_paid
-- This means you CANNOT pass balance_due in INSERT/UPDATE payloads —
-- Postgres computes it automatically. The fix already made in
-- 1_POS.py adds balance_due to the insert dict, BUT because the
-- column is GENERATED, Supabase will reject it with:
--   "cannot insert a non-DEFAULT value into column balance_due"
-- SOLUTION: Remove "balance_due" from the INSERT in 1_POS.py and
-- rely on the generated column. The Orders/Home pages will still
-- read the correct value from the DB.
-- If you prefer to store it manually, replace the column definition
-- above with:
--   balance_due  numeric(12,2) not null default 0,
-- and keep the insert fix in 1_POS.py as-is.


-- ============================================================
-- SEED DATA  (optional demo rows — safe to skip in production)
-- ============================================================

insert into suppliers (name, phone) values
    ('Fabric House Ltd',    '+250 788 000 001'),
    ('Metro Supplies',      '+250 788 000 002'),
    ('General Traders',     '+250 788 000 003')
on conflict do nothing;

insert into catalog (name, type, uom, current_landed_cost, default_sell_price) values
    ('Cotton Fabric',       'Material', 'Meters',    1200.00, 1800.00),
    ('Polyester Lining',    'Material', 'Meters',     800.00, 1200.00),
    ('Zipper 20cm',         'Material', 'Pieces',     150.00,  250.00),
    ('Button Set (12pcs)',  'Material', 'Pieces',     200.00,  350.00),
    ('T-Shirt (finished)',  'Product',  'Pieces',    3500.00, 5500.00),
    ('Tailoring Service',   'Service',  'Flat Rate', 2000.00, 3500.00)
on conflict do nothing;
