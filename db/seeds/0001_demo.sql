
-- Nyra Service Tool :: demo seed (2 organisations)
-- Idempotent: fixed ids + ON CONFLICT DO NOTHING.

begin;

insert into tenant (id, slug, name) values
  (1, 'nyra-demo',      'Nyra Demo Corporation'),
  (2, 'nyra-demo-mfg',  'Nyra Demo Manufacturing (vertical demo)')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- calendars
insert into business_calendar (id, tenant_id, name, timezone, work_days, work_start, work_end, holidays) values
  (1, 1, 'India Business Hours (9-6)', 'Asia/Kolkata', '{1,2,3,4,5}', '09:00', '18:00', '["2026-01-26","2026-03-04","2026-08-15","2026-10-02","2026-10-20","2026-11-08","2026-12-25"]'),
  (2, 1, '24x7 Critical Services',     'Asia/Kolkata', '{1,2,3,4,5,6,7}', '00:00', '23:59', '[]'),
  (3, 2, 'Plant Shift Hours',          'Asia/Kolkata', '{1,2,3,4,5,6}', '06:00', '22:00', '[]')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- org units
insert into org_unit (id, tenant_id, kind, name, code, parent_id, timezone, country, state, city) values
  (1, 1, 'company',    'Nyra Demo Corporation', 'NDC', null, 'Asia/Kolkata', 'India', 'Karnataka', 'Bengaluru'),
  (2, 1, 'location',   'Bengaluru HQ', 'BLR', 1, 'Asia/Kolkata', 'India', 'Karnataka', 'Bengaluru'),
  (3, 1, 'location',   'Mumbai Branch', 'BOM', 1, 'Asia/Kolkata', 'India', 'Maharashtra', 'Mumbai'),
  (4, 1, 'location',   'Hyderabad DC', 'HYD', 1, 'Asia/Kolkata', 'India', 'Telangana', 'Hyderabad'),
  (5, 1, 'department', 'Information Technology', 'IT', 1, 'Asia/Kolkata', null, null, null),
  (6, 1, 'department', 'Finance & Accounts', 'FIN', 1, 'Asia/Kolkata', null, null, null),
  (7, 1, 'department', 'Human Resources', 'HR', 1, 'Asia/Kolkata', null, null, null),
  (8, 1, 'department', 'Sales', 'SLS', 1, 'Asia/Kolkata', null, null, null),
  (9, 1, 'cost_center','CC-IT-1001', 'CC-IT-1001', 5, 'Asia/Kolkata', null, null, null),
  (10,1, 'cost_center','CC-FIN-2001','CC-FIN-2001', 6, 'Asia/Kolkata', null, null, null),
  (11,2, 'company',    'Nyra Demo Manufacturing', 'NDM', null, 'Asia/Kolkata', 'India', 'Tamil Nadu', 'Chennai'),
  (12,2, 'location',   'Chennai Plant 1', 'MAA1', 11, 'Asia/Kolkata', 'India', 'Tamil Nadu', 'Chennai')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- teams (with distribution list addresses)
insert into team (id, tenant_id, name, code, tier, domain, email, mailbox_mode, shared_mailbox, calendar_id, skills, description) values
  (1, 1, 'Service Desk L1',        'SD-L1', 'l1', 'it', 'servicedesk-l1@example.com', 'relay', 'helpdesk@example.com', 1,
      '{password_reset,access_request,general_enquiry}', 'First line: intake, triage, known-fix and password/access fulfilment'),
  (2, 1, 'Desktop & Endpoint L2',  'EP-L2', 'l2', 'it', 'endpoint-l2@example.com', 'app_expanded', null, 1,
      '{windows,macos,laptop,vpn,printing,software_install}', 'Second line endpoint and user devices'),
  (3, 1, 'Network & Connectivity L2','NET-L2','l2','it', 'network-l2@example.com', 'app_expanded', null, 2,
      '{lan,wan,wifi,vpn,firewall,load_balancer}', 'Network operations, 24x7 for P1'),
  (4, 1, 'Applications L3',        'APP-L3', 'l3', 'it', 'apps-l3@example.com', 'relay', null, 1,
      '{erp,crm,oracle,sap,web_apps}', 'Application support and vendor escalation'),
  (5, 1, 'Database & Server L3',   'DBA-L3', 'l3', 'it', 'dba-l3@example.com', 'relay', null, 2,
      '{oracle,sqlserver,postgres,linux,windows_server}', 'Database and server platform'),
  (6, 1, 'Security Operations',    'SEC-OPS','l2', 'security', 'soc@example.com', 'app_expanded', 'soc@example.com', 2,
      '{incident_response,malware,phishing,access_review}', 'Security incidents and escalations'),
  (7, 1, 'HR Shared Services',     'HR-SS', 'business', 'hr', 'hr-helpdesk@example.com', 'relay', null, 1,
      '{payroll,leave,onboarding,benefits,letters}', 'Employee HR requests (non-IT request model)'),
  (8, 1, 'Finance Support',        'FIN-SS','business', 'finance', 'finance-helpdesk@example.com', 'relay', null, 1,
      '{invoice,expense,purchase_order,vendor_creation}', 'AP/AR and procurement requests'),
  (9, 1, 'Facilities',             'FAC',   'business', 'facilities', 'facilities@example.com', 'relay', null, 1,
      '{seat,access_card,housekeeping,cafeteria}', 'Workplace requests'),
  (10,1, 'IT Leadership',          'IT-LEAD','governance','it', 'it-leadership@example.com', 'relay', null, 1,
      '{}', 'Escalation and governance; receives major incident comms'),
  (11,2, 'Plant IT Support',       'PLT-IT','l1', 'it', 'plant-it@example.com', 'relay', null, 3,
      '{shopfloor,scada,label_printer}', 'Plant-floor IT'),
  (12,1, 'Vendor - AcmeCloud',     'VEN-ACME','vendor','it', 'support@acmecloud.example', 'relay', null, 2,
      '{}', 'External vendor support queue (shared mailbox style intake)')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- people
insert into person (id, tenant_id, party_type, user_name, first_name, last_name, display_name, email, phone, mobile, caller_id,
                    job_title, employee_id, department_id, company_id, location_id, cost_center, grade, worker_type,
                    manager_id, roles, access_level, team_id, is_vip, language) values
  -- IT agents
  (1, 1, 'employee', 'gagan',  'Gagan',  'R',   'Gagan R',            'gagan@example.com',    '+91-80-4000-1001', '+91-98450-00001', '+918040001001', 'IT Service Manager',      'E1001', 5, 1, 2, 'CC-IT-1001', 'M3', 'full_time', null, '{admin,service_owner,agent_l2}', 'privileged', 3, false, 'en'),
  (2, 1, 'employee', 'priya.s','Priya',  'Sharma','Priya Sharma',      'priya.s@example.com',  '+91-80-4000-1002', '+91-98450-00002', '+918040001002', 'Service Desk Lead',       'E1002', 5, 1, 2, 'CC-IT-1001', 'M2', 'full_time', 1,    '{team_lead,agent_l1,agent_l2}','elevated', 1, false, 'en'),
  (3, 1, 'employee', 'arjun.m','Arjun',  'Menon', 'Arjun Menon',       'arjun.m@example.com',  '+91-80-4000-1003', '+91-98450-00003', null,            'Service Desk Analyst',    'E1003', 5, 1, 2, 'CC-IT-1001', 'E4', 'full_time', 2,    '{agent_l1}','standard', 1, false, 'en'),
  (4, 1, 'employee', 'neha.k', 'Neha',   'Kulkarni','Neha Kulkarni',   'neha.k@example.com',   '+91-22-4000-2001', '+91-98450-00004', null,            'Endpoint Engineer',       'E1004', 5, 1, 3, 'CC-IT-1001', 'E5', 'full_time', 1,    '{agent_l2}','elevated', 2, false, 'en'),
  (5, 1, 'employee', 'rahul.v','Rahul',  'Verma',  'Rahul Verma',       'rahul.v@example.com',  '+91-80-4000-1005', '+91-98450-00005', null,            'Network Engineer',        'E1005', 5, 1, 2, 'CC-IT-1001', 'E5', 'full_time', 1,    '{agent_l2}','elevated', 3, false, 'en'),
  (6, 1, 'employee', 'sara.f', 'Sara',   'Fernandes','Sara Fernandes',  'sara.f@example.com',   '+91-40-4000-3001', '+91-98450-00006', null,            'Application Support Lead','E1006', 5, 1, 4, 'CC-IT-1001', 'M1', 'full_time', 1,    '{agent_l3,service_owner}','elevated', 4, false, 'en'),
  (7, 1, 'employee', 'vikram.s','Vikram','Singh',  'Vikram Singh',      'vikram.s@example.com', '+91-80-4000-1007', '+91-98450-00007', null,            'DBA',                     'E1007', 5, 1, 2, 'CC-IT-1001', 'E5', 'full_time', 1,    '{agent_l3}','elevated', 5, false, 'en'),
  (8, 1, 'employee', 'deepa.n','Deepa',  'Nair',   'Deepa Nair',        'deepa.n@example.com',  '+91-80-4000-1008', '+91-98450-00008', null,            'Security Analyst',        'E1008', 5, 1, 2, 'CC-IT-1001', 'E5', 'full_time', 1,    '{agent_l2}','elevated', 6, false, 'en'),
  (9, 1, 'employee', 'hr.help','Meera',  'Iyer',   'Meera Iyer',        'meera.i@example.com',  '+91-80-4000-1009', '+91-98450-00009', null,            'HR Service Lead',         'E1009', 7, 1, 2, null,         'M1', 'full_time', 1,    '{agent_l1,team_lead}','standard', 7, false, 'en'),
  (10,1, 'employee', 'fin.help','Rohit', 'Bansal', 'Rohit Bansal',      'rohit.b@example.com',  '+91-80-4000-1010', '+91-98450-00010', null,            'Finance Ops Analyst',     'E1010', 6, 1, 2, 'CC-FIN-2001','E4', 'full_time', 1,   '{agent_l1}','standard', 8, false, 'en'),
  -- end users
  (20,1, 'employee', 'meera.d','Meera',  'Deshpande','Meera Deshpande', 'meera.d@example.com',  '+91-22-4010-1001', '+91-98450-00101', '+918040101001', 'VP Sales',                'E2001', 8, 1, 3, null,         'M5', 'full_time', 1,    '{end_user}','elevated', null, true,  'en'),
  (21,1, 'employee', 'kiran.p','Kiran',  'Patel',  'Kiran Patel',       'kiran.p@example.com',  '+91-80-4010-1002', '+91-98450-00102', null,            'Senior Financial Analyst','E2002', 6, 1, 2, 'CC-FIN-2001','E4', 'full_time', 1,   '{end_user}','standard', null, false, 'en'),
  (22,1, 'employee', 'anita.r','Anita',  'Rao',    'Anita Rao',         'anita.r@example.com',  '+91-40-4010-1003', '+91-98450-00103', null,            'Systems Administrator',   'E2003', 5, 1, 4, 'CC-IT-1001', 'E5', 'full_time', 1,    '{end_user}','elevated', null, false, 'en'),
  (23,1, 'employee', 'sam.c',  'Sam',    'Chen',   'Sam Chen',          'sam.c@example.com',    '+91-80-4010-1004', '+91-98450-00104', null,            'Marketing Manager',       'E2004', 8, 1, 2, null,         'M2', 'full_time', 1,    '{end_user}','standard', null, false, 'en'),
  (24,1, 'contractor','max.w','Max',     'Weber',  'Max Weber (contract)','max.w@vendor.example','+91-80-4010-1005','+91-98450-00105', null,            'Contract Developer',      'C3001', 5, 1, 2, 'CC-IT-1001', 'C2', 'contract', 1,    '{end_user}','restricted', null, false, 'en'),
  (30,1, 'vendor_contact', null, null,   null,    'AcmeCloud Support Desk','support@acmecloud.example','+1-408-555-0100', null, null,      'Vendor Support',          null,   null, null, null, null, null, 'vendor', null, '{end_user}','restricted', null, false, 'en'),
  (40,2, 'employee', 'plant.lead','Suresh','Kumar','Suresh Kumar',      'suresh.k@mfg.example', '+91-44-4020-1001', '+91-98450-00201', null,            'Plant IT Engineer',       'E4001', null, 11, 12, null, 'E4', 'full_time', null, '{agent_l1,team_lead}','standard', 11, false, 'en'),
  (41,2, 'employee', 'line.op','Lakshmi', 'Raman', 'Lakshmi Raman',     'lakshmi.r@mfg.example','+91-44-4020-1002', '+91-98450-00202', null,            'Line Supervisor',         'E4002', null, 11, 12, null, 'E3', 'full_time', null, '{end_user}','standard', null, false, 'en')
on conflict (id) do nothing;

update person set manager_id = 1 where tenant_id = 1 and manager_id is null and id between 20 and 23;

insert into team_member (id, team_id, person_id, team_role, is_primary, capacity) values
  (1, 1, 2, 'manager', true, 40), (2, 1, 3, 'member', true, 40),
  (3, 2, 4, 'manager', true, 40),
  (4, 3, 5, 'manager', true, 40), (5, 3, 1, 'backup', false, 20),
  (6, 4, 6, 'manager', true, 40),
  (7, 5, 7, 'manager', true, 40),
  (8, 6, 8, 'manager', true, 40),
  (9, 7, 9, 'manager', true, 40),
  (10, 8, 10, 'manager', true, 40),
  (11, 11, 40, 'manager', true, 40),
  (12, 10, 1, 'member', false, 10)
on conflict (id) do nothing;

-- ---------------------------------------------------------------- sla policies
insert into sla_policy (id, tenant_id, name, applies_to, match_priority, response_minutes, resolution_minutes, update_interval_minutes, use_business_hours, calendar_id, at_risk_percent) values
  (1, 1, 'IT - P1 Critical (24x7)', 'incident', '{1}', 15,  240,  60, false, 2, 75),
  (2, 1, 'IT - P2 High (24x7)',     'incident', '{2}', 30,  480,  120, false, 2, 75),
  (3, 1, 'IT - P3 Medium (BizHrs)','incident', '{3}', 240, 2880, 480, true,  1, 80),
  (4, 1, 'IT - P4 Low (BizHrs)',    'incident', '{4,5}', 480, 7200, 960, true, 1, 80),
  (5, 1, 'HR requests (BizHrs)',    'request',  '{3,4,5}', 480, 4800, 1440, true, 1, 80),
  (6, 1, 'Finance requests (BizHrs)','request', '{3,4,5}', 480, 5760, 1440, true, 1, 80),
  (7, 2, 'Plant IT (shift hours)',  'incident', '{1,2,3,4,5}', 30, 480, 240, true, 3, 75)
on conflict (id) do nothing;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'team_default_sla_fk') then
    alter table team add constraint team_default_sla_fk
      foreign key (default_sla_policy_id) references sla_policy(id) on delete set null;
  end if;
end $$;
update team set default_sla_policy_id = case when tier = 'l1' then 3 when tier in ('l2','l3') then 2 else 4 end where default_sla_policy_id is null;

-- ---------------------------------------------------------------- taxonomy (IT + HR + Finance)
insert into taxonomy (id, tenant_id, kind, domain, name, parent_id, default_team_id, default_priority, keywords) values
  (1, 1, 'category', 'it', 'Hardware', null, 2, 3, '{laptop,desktop,printer,monitor,keyboard,battery,charger}'),
  (2, 1, 'subcategory','it','Laptop', 1, 2, 3, '{laptop,notebook,thinkpad,macbook,battery,charger}'),
  (3, 1, 'subcategory','it','Desktop',1, 2, 3, '{desktop,workstation,monitor,docking}'),
  (4, 1, 'subcategory','it','Printer / Scanner',1, 2, 4, '{printer,scanner,toner,jam,print queue}'),
  (5, 1, 'category', 'it', 'Software', null, 4, 3, '{software,license,install,crash,error}'),
  (6, 1, 'subcategory','it','Application Error',5, 4, 2, '{error,exception,not responding,crash,500}'),
  (7, 1, 'subcategory','it','Software Install / License',5, 2, 4, '{install,license,activation,upgrade}'),
  (8, 1, 'category', 'it', 'Network', null, 3, 2, '{network,internet,slow,latency}'),
  (9, 1, 'subcategory','it','VPN / Remote Access',8, 3, 2, '{vpn,remote,anyconnect,tunnel,radius}'),
  (10,1, 'subcategory','it','Wi-Fi',8, 3, 3, '{wifi,wireless,ssid,authentication}'),
  (11,1, 'subcategory','it','WAN / Internet Link',8, 3, 1, '{wan,link,isp,outage,circuit}'),
  (12,1, 'category', 'it', 'Access & Identity', null, 1, 3, '{access,password,login,locked,account,permission}'),
  (13,1, 'subcategory','it','Password Reset',12, 1, 4, '{password,reset,forgot,expired,locked}'),
  (14,1, 'subcategory','it','Account Lockout / MFA',12, 1, 3, '{locked,mfa,authenticator,otp,2fa}'),
  (15,1, 'subcategory','it','Access Request (new/changed)',12, 1, 4, '{access request,share drive,application access,role}'),
  (16,1, 'category', 'it', 'Email & Collaboration', null, 2, 3, '{email,outlook,teams,calendar,mailbox}'),
  (17,1, 'subcategory','it','Mailbox / Distribution List',16, 2, 3, '{mailbox,distribution list,shared mailbox,quota}'),
  (18,1, 'category', 'it', 'Database & Server', null, 5, 2, '{database,server,postgres,oracle,sqlserver,disk full}'),
  (19,1, 'subcategory','it','Database Down / Slow',18, 5, 1, '{database down,ora-,cannot connect,slow query,tablespace}'),
  (20,1, 'category', 'it', 'Security', null, 6, 1, '{phishing,malware,ransomware,suspicious,breach}'),
  (21,1, 'subcategory','it','Phishing / Suspicious Email',20, 6, 1, '{phishing,spam,suspicious link,spoof}'),
  (22,1, 'category', 'it', 'How Do I / Enquiry', null, 1, 5, '{how to,question,guidance,request information}'),
  (30,1, 'category', 'hr', 'Payroll', null, 7, 3, '{payroll,salary,payslip,tax,deduction}'),
  (31,1, 'subcategory','hr','Payslip / Tax Query',30, 7, 4, '{payslip,form 16,tds,reimbursement}'),
  (32,1, 'category', 'hr', 'Leave & Attendance', null, 7, 4, '{leave,attendance,holiday,comp off}'),
  (33,1, 'category', 'hr', 'Onboarding / Offboarding', null, 7, 3, '{onboarding,new joiner,exit,fulfilment,assets}'),
  (34,1, 'category', 'hr', 'Letters & Documents', null, 7, 4, '{experience letter,address proof,visa letter,verification}'),
  (40,1, 'category', 'finance', 'Invoice / Payments', null, 8, 3, '{invoice,payment,ap,bill,duplicate}'),
  (41,1, 'category', 'finance', 'Purchase Requisition', null, 8, 4, '{purchase,pr,po,quote,vendor}'),
  (42,1, 'category', 'finance', 'Expense Reimbursement', null, 8, 4, '{expense,reimbursement,claim,concur}'),
  (50,1, 'category', 'facilities', 'Workplace', null, 9, 4, '{seat,desk,chair,housekeeping,access card,cafeteria}'),
  (60,2, 'category', 'manufacturing', 'Shop-floor Equipment IT', null, 11, 2, '{scada,plc,label printer,hmi,terminal,shopfloor}'),
  (61,2, 'category', 'manufacturing', 'Line Terminal / HMI', null, 11, 2, '{terminal,hmi,touchscreen,scanner}'),
  (62,2, 'category', 'manufacturing', 'EHS / Safety Incident', null, 11, 1, '{safety,injury,near miss,spill,fire}')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- services + CIs
insert into service (id, tenant_id, name, service_type, domain, owner_id, criticality, support_team_id, sla_policy_id, status, description) values
  (1, 1, 'Corporate Email & Calendar', 'business', 'it', 6, 'critical', 4, 1, 'live', 'Mail, calendar and Teams for all staff'),
  (2, 1, 'Core ERP (Finance & Supply Chain)', 'business', 'it', 6, 'critical', 4, 1, 'live', 'Order-to-cash and procure-to-pay'),
  (3, 1, 'WAN & Site Connectivity', 'technical', 'it', 1, 'critical', 3, 1, 'live', 'Inter-site links and internet egress'),
  (4, 1, 'End-User Computing', 'technical', 'it', 1, 'high', 2, 2, 'live', 'Laptops, desktops, printing, endpoint security'),
  (5, 1, 'Identity & Access', 'technical', 'it', 1, 'high', 1, 3, 'live', 'Directory, SSO, MFA, joiner-mover-leaver'),
  (6, 1, 'HR Employee Services', 'business', 'hr', 9, 'high', 7, 5, 'live', 'Payroll queries, leave, letters, onboarding'),
  (7, 1, 'Finance Shared Services', 'business', 'finance', 10, 'high', 8, 6, 'live', 'AP/AR, expense, procurement requests'),
  (8, 2, 'Plant 1 Shop-floor IT', 'technical', 'manufacturing', 40, 'critical', 11, 7, 'live', 'Line terminals, SCADA connectivity, label printing')
on conflict (id) do nothing;

insert into ci (id, tenant_id, name, ci_class, environment, operational_status, criticality, owner_id, support_team_id, location_id, parent_id, discovered, attributes) values
  (1, 1, 'erp-app-01', 'application', 'prod', 'operational', 'critical', 6, 4, 4, null, true, '{"version":"12.2.9","vendor":"AcmeERP"}'),
  (2, 1, 'erp-db-01', 'database', 'prod', 'operational', 'critical', 7, 5, 4, 1, true, '{"engine":"oracle","version":"19c","size_gb":2400}'),
  (3, 1, 'mail-gw-01', 'application', 'prod', 'operational', 'critical', 6, 4, 4, null, true, '{"role":"smtp_gateway"}'),
  (4, 1, 'wan-router-blr', 'network_device', 'prod', 'operational', 'critical', 5, 3, 2, null, true, '{"model":"ASR1002-X","circuit":"ISP-A"}'),
  (5, 1, 'wan-router-bom', 'network_device', 'prod', 'operational', 'critical', 5, 3, 3, null, true, '{"model":"ASR1002-X","circuit":"ISP-B"}'),
  (6, 1, 'nyra-vpn-concentrator', 'network_device', 'prod', 'operational', 'high', 5, 3, 2, 4, true, '{"sessions_max":2000}'),
  (7, 1, 'file-print-srv-01', 'server', 'prod', 'operational', 'medium', 4, 2, 2, null, true, '{"os":"Windows Server 2022"}'),
  (8, 1, 'hr-portal-01', 'application', 'prod', 'operational', 'medium', 9, 4, 4, null, true, '{"vendor":"HRCloud"}'),
  (9, 1, 'blr-floor3-ap-11', 'network_device', 'prod', 'operational', 'medium', 5, 3, 2, null, true, '{"type":"wifi_ap","ssid":"NDC-Corp"}'),
  (10,1, 'LAPTOP-E2401', 'hardware', 'prod', 'operational', 'low', 4, 2, 3, null, true, '{"model":"ThinkPad T14","assigned_to":"meera.d@example.com","warranty_end":"2027-06-30"}')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- numbering sequences
insert into numbering_sequence (id, tenant_id, key, prefix, next_value, padding) values
  (1, 1, 'incident', 'INC', 11, 7),
  (2, 1, 'problem',  'PRB', 1, 7),
  (3, 1, 'change',   'CHG', 1, 7),
  (4, 1, 'request',  'REQ', 1, 7),
  (5, 1, 'ritm',     'RITM', 1, 7),
  (6, 1, 'task',     'TASK', 1, 7),
  (7, 1, 'kb',       'KB', 6, 5),
  (8, 2, 'incident', 'INC', 3, 7),
  (9, 2, 'kb',       'KB', 1, 5)
on conflict (id) do nothing;

-- ---------------------------------------------------------------- demo records
insert into record (id, tenant_id, number, type, short_description, description, state, opened_by, opened_at, caller_id, channel, assignment_group_id, assignee_id, priority, urgency, impact, category_id, subcategory_id, service_id, ci_id, location_id, department_id, company_id, major_incident, escalation, sla_state, sla_policy_id, workaround, resolution_notes, resolution_code, tags, ai) values
  ('1', '1', 'INC0000001', 'incident', 'VPN disconnects every 5 minutes after the client update', 'Since the 7.4 client update yesterday evening, VPN drops every ~5 minutes. Tried reinstall, same behaviour. Working from Mumbai branch.', 'in_progress', '20', now() - interval '6 hours', '20', 'email', '3', '5', '2', '2', '2', '8', '9', '3', '6', '3', '8', '1', false, false, 'ok', '2', null, null, null, '{vpn,remote-work}', '{"category_suggestion": 9, "confidence": 0.91, "summary": "VPN instability after 7.4 client update", "sentiment": "negative", "model": "seed"}'),
  ('2', '1', 'INC0000002', 'incident', 'ERP invoice posting hangs at 90% for all users', 'Multiple finance users report invoice posting stuck at 90%. Started 07:40. Month-end closing today - urgent.', 'in_progress', '21', now() - interval '4 hours', '21', 'portal', '4', '6', '1', '1', '1', '5', '6', '2', '1', '4', '6', '1', true, true, 'at_risk', '1', 'Workaround: batch posting via the backend job completes; the UI path fails.', null, null, '{erp,month-end,major}', '{"category_suggestion": 6, "confidence": 0.88, "sentiment": "negative", "duplicate_of": null, "model": "seed"}'),
  ('3', '1', 'INC0000003', 'incident', 'Locked out of email after password change', null, 'resolved', '23', now() - interval '26 hours', '23', 'phone', '1', '3', '4', '3', '3', '12', '14', '5', null, '2', '8', '1', false, false, 'ok', '3', null, 'Account unlocked in AD, cached credentials cleared on device, user re-authenticated successfully.', 'FIXED_KNOWN_ERROR', '{password,locked}', '{"category_suggestion": 14, "confidence": 0.95, "model": "seed"}'),
  ('4', '1', 'INC0000004', 'incident', 'Wi-Fi authentication failures on floor 3 Bengaluru', 'Several users on floor 3 cannot authenticate to NDC-Corp. Started after the AP firmware window.', 'in_progress', '22', now() - interval '90 minutes', '22', 'portal', '3', '5', '2', '2', '3', '8', '10', '3', '9', '2', '5', '1', false, false, 'at_risk', '2', null, null, null, '{wifi,floor3}', '{"category_suggestion": 10, "confidence": 0.9, "model": "seed"}'),
  ('5', '1', 'INC0000005', 'incident', 'Phishing email claiming to be from the CEO - credential harvesting link', 'User forwarded a message with a link to a fake OWA login page. Not clicked.', 'new', '24', now() - interval '35 minutes', '24', 'email', '6', null, '1', '1', '2', '20', '21', '1', '3', '2', '5', '1', false, true, 'ok', '1', null, null, null, '{security,phishing}', '{"category_suggestion": 21, "confidence": 0.97, "sentiment": "anxious", "model": "seed"}'),
  ('6', '1', 'INC0000006', 'incident', 'Need Adobe Acrobat Pro licence for contract review', 'Requesting a licence for the legal review workflow.', 'on_hold', '21', now() - interval '50 hours', '21', 'portal', '2', null, '4', '3', '3', '5', '7', '4', null, '3', '6', '1', false, false, 'ok', '4', null, null, null, '{}', '{"category_suggestion": 7, "confidence": 0.83, "model": "seed"}'),
  ('7', '1', 'INC0000007', 'incident', 'Printer on 3rd floor jamming on every duplex job', null, 'closed', '23', now() - interval '9 days', '23', 'walk_up', '2', '4', '4', '3', '3', '1', '4', '4', '7', '2', '8', '1', false, false, 'ok', '4', null, 'Duplex unit replaced by the field engineer.', 'FIXED_HARDWARE', '{}', '{"category_suggestion": 4, "confidence": 0.92, "model": "seed"}'),
  ('8', '1', 'INC0000008', 'incident', 'Payslip for August not visible in the HR portal', 'Employee cannot see the August payslip while colleagues can.', 'in_progress', '20', now() - interval '20 hours', '20', 'email', '7', '9', '4', '3', '3', '30', '31', '6', '8', '3', '7', '1', false, false, 'ok', '5', null, null, null, '{}', '{"category_suggestion": 31, "confidence": 0.86, "model": "seed"}'),
  ('9', '2', 'INC0000001', 'incident', 'Line 2 label printer not printing batch labels', 'Production stopped on Line 2 - labels not printing from the terminal.', 'in_progress', '41', now() - interval '2 hours', '41', 'phone', '11', '40', '1', '1', '2', '60', '61', '8', null, '12', null, '11', false, false, 'at_risk', '7', null, null, null, '{shopfloor,production-stop}', '{"category_suggestion": 61, "confidence": 0.89, "model": "seed"}'),
  ('10', '2', 'INC0000002', 'incident', 'Safety near-miss reported at packing station 4', 'Pallet shifted during packing - no injury, near miss reported by supervisor.', 'new', '41', now() - interval '30 minutes', '41', 'portal', '11', null, '2', '1', '2', '62', null, null, null, '12', null, '11', false, false, 'ok', '7', null, null, null, '{ehs,safety}', '{"category_suggestion": 62, "confidence": 0.8, "model": "seed"}')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- child tasks (parent/child rollup)
insert into record (id, tenant_id, number, type, parent_id, root_id, short_description, state, opened_by, caller_id, channel, assignment_group_id, assignee_id, priority, urgency, impact, category_id, subcategory_id, service_id, sla_state, sla_policy_id) values
  (11, 1, 'INCIDENT-TASK-1', 'task', 2, 2, 'Capture application logs from erp-app-01 during the hang window', 'in_progress', 21, 21, 'agent', 4, 6, 2, 2, 2, 6, 1, 1, 'ok', 2),
  (12, 2, 'INCIDENT-TASK-2', 'task', 9, 9, 'Check print spooler service and driver on the line terminal', 'new', 41, 41, 'agent', 11, 40, 1, 1, 2, 60, 61, 8, 'ok', 7)
on conflict (id) do nothing;

-- ---------------------------------------------------------------- activity: work notes, public comments, inbound email
insert into record_comment (id, tenant_id, record_id, author_id, kind, body, source, is_internal, created_at) values
  (1, 1, 1, 5, 'work_note', 'Reproduced on two devices. Same 5-minute drop pattern. Suspect MTU/fragment issue in the 7.4 client.', 'agent', true, now() - interval '3 hours'),
  (2, 1, 1, 2, 'public_comment', 'Thank you for reporting - we have reproduced the issue and are testing a client rollback. We will update you within 2 hours.', 'agent', false, now() - interval '2 hours 40 minutes'),
  (3, 1, 1, 20, 'email_in', 'Update please - this is blocking my customer calls today.', 'email', false, now() - interval '40 minutes'),
  (4, 1, 2, 6, 'work_note', 'UI path hangs at 90%; the backend posting job completes. Vendor case raised (ACME-44821). P1 bridge at 09:00.', 'agent', true, now() - interval '3 hours'),
  (5, 1, 2, 1, 'system', 'Major incident declared by Gagan R. Stakeholder notifications queued to it-leadership@example.com.', 'system', true, now() - interval '3 hours 50 minutes'),
  (6, 1, 5, 8, 'work_note', 'Checking mail gateway headers; initiating sender block and an org-wide advisory.', 'agent', true, now() - interval '20 minutes'),
  (7, 2, 9, 40, 'work_note', 'Confirmed spooler service stopped on the line terminal. Restarting and checking the driver version.', 'agent', true, now() - interval '90 minutes')
on conflict (id) do nothing;

insert into record_relationship (id, tenant_id, record_id, related_id, relation) values
  (1, 1, 3, 1, 'relates_to'),
  (2, 1, 2, 5, 'relates_to')
on conflict (id) do nothing;

-- SLA target backfill for the seeded records.
-- prototype depth: plain interval arithmetic (no business-calendar walk) so the demo has live SLA clocks.
update record r
   set response_due_at = coalesce(r.response_due_at, r.opened_at + make_interval(mins => sp.response_minutes)),
       resolve_due_at  = coalesce(r.resolve_due_at,  r.opened_at + make_interval(mins => sp.resolution_minutes))
  from sla_policy sp
 where sp.id = r.sla_policy_id
   and sp.resolution_minutes is not null
   and r.resolve_due_at is null;

update record
   set response_met = (response_at is not null and response_due_at is not null and response_at <= response_due_at),
       resolution_met = (resolved_at is not null and resolve_due_at is not null and resolved_at <= resolve_due_at);

-- ---------------------------------------------------------------- knowledge
insert into kb_article (id, tenant_id, number, title, summary, body, state, visibility, owner_id, category_id, service_id, tags, version, hit_count, helpful_count, not_helpful_count, published_at, review_due_at, created_by) values
  (1, 1, 'KB00001', 'How to reset your own password from the portal', 'Self-service password reset steps for AD-synced accounts.',
   'Steps: 1) Open the help centre. 2) Choose Password reset. 3) Verify with MFA. 4) Set a new password of at least 14 characters. 5) Update saved credentials on mobile devices. If MFA is unavailable, raise an access request and the service desk will verify your identity by callback.',
   'published', 'portal', 2, 12, 5, '{password,self-service,ad}', 3, 412, 96, 7, now() - interval '40 days', (now() + interval '50 days')::date, 2),
  (2, 1, 'KB00002', 'VPN keeps disconnecting after the 7.4 client update - workaround', 'Known workaround for VPN drops after client 7.4.',
   'Until the patched client (7.4.2) is published: 1) Disable IPv6 on the VPN adapter. 2) Set MTU to 1300 on the adapter. 3) Reconnect and confirm stability for 15 minutes. Engineering has reproduced the fault; rollback package is available on the software portal.',
   'published', 'portal', 5, 8, 3, '{vpn,workaround,mtu}', 2, 188, 61, 4, now() - interval '1 day', (now() + interval '89 days')::date, 5),
  (3, 1, 'KB00003', 'Recognising a phishing email and what to do', 'How to spot phishing and report it in one click.',
   'Report any message that asks for credentials, payment or urgency outside normal process. Never click links in unexpected mail. Use the Report Phishing button in the mail client. The security team will confirm within 30 minutes and quarantine similar mail org-wide.',
   'published', 'public', 8, 20, 1, '{phishing,security,awareness}', 1, 95, 40, 2, now() - interval '12 days', (now() + interval '78 days')::date, 8),
  (4, 1, 'KB00004', 'How to request a new laptop or accessory', 'Catalogue request steps and standard models.',
   'Open the help centre, choose Hardware, then Laptop request. Provide the standard model code, delivery location and the cost centre. Manager approval is required above tier 2. Standard delivery is 5 business days in Bengaluru and Mumbai.',
   'published', 'portal', 4, 1, 4, '{laptop,hardware,catalogue}', 1, 130, 51, 3, now() - interval '20 days', (now() + interval '70 days')::date, 4),
  (5, 1, 'KB00005', 'ERP invoice posting stuck at 90% (draft runbook)', 'Agent runbook while vendor case is open.',
   'INTERNAL: 1) Confirm batch job completes in the scheduler. 2) Capture the application log window. 3) If UI path fails for more than 10 users, declare major incident and open a bridge. 4) Use backend batch posting as the workaround with finance sign-off. Draft - pending review.',
   'in_review', 'internal', 6, 5, 2, '{erp,runbook,major}', 1, 34, 12, 1, null, (now() + interval '10 days')::date, 6)
on conflict (id) do nothing;

insert into kb_feedback (id, article_id, person_id, helpful, comment) values
  (1, 1, 20, true, 'Worked first time.'),
  (2, 2, 23, true, 'MTU change fixed it for me.'),
  (3, 2, 22, false, 'Did not work on macOS.')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- csat
insert into csat_survey (id, tenant_id, record_id, person_id, score, comment, sent_at, responded_at) values
  (1, 1, 3, 23, 5, 'Fast and clear, thank you.', now() - interval '25 hours', now() - interval '24 hours'),
  (2, 1, 7, 23, 4, 'Took two visits to the printer.', now() - interval '8 days', now() - interval '8 days' + interval '3 hours')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- notification templates + audiences
insert into notification_template (id, tenant_id, code, event, channel, subject, body, version) values
  (1, 1, 'incident.created',            'record.created',              'email', '[{{number}}] We have logged your request - {{short_description}}', 'Hello {{caller_first_name}},

Your request has been logged as {{number}}.
Summary: {{short_description}}
Priority: {{priority_label}} (response target {{response_due}}, resolution target {{resolve_due}})
Assigned team: {{assignment_group}}

You can track it here: {{portal_link}}
Reply to this email to add information.

Nyra Service Desk', 1),
  (2, 1, 'incident.assigned_group',     'record.assigned_group',       'email', '[{{number}}] {{priority_label}} assigned to {{assignment_group}}', 'A ticket has been assigned to your team.

{{number}} - {{short_description}}
Caller: {{caller_name}} ({{caller_vip}})
Priority: {{priority_label}} / Impact {{impact}} / Urgency {{urgency}}
Response target: {{response_due}} | Resolution target: {{resolve_due}}
Location: {{location}} | Service: {{service}}

Take it: {{record_link}}', 1),
  (3, 1, 'incident.assigned_you',       'record.assigned_user',        'email', '[{{number}}] Assigned to you - {{short_description}}', '{{assignee_first_name}}, this ticket is now assigned to you.

{{number}} - {{short_description}}
Caller: {{caller_name}} | Priority: {{priority_label}}
Resolution target: {{resolve_due}} ({{sla_state}})
Handover notes: {{handover_notes}}

Open: {{record_link}}', 1),
  (4, 1, 'incident.comment_public',     'record.comment_public',       'email', '[{{number}}] Update from the service desk', 'Hello {{caller_first_name}},

{{author_name}} added an update to {{number}}:

"{{comment_body}}"

Current state: {{state}}
Reply to this email to respond.

Nyra Service Desk', 1),
  (5, 1, 'incident.resolved',           'record.resolved',             'email', '[{{number}}] Resolved - please confirm', 'Hello {{caller_first_name}},

{{number}} has been marked resolved.

Resolution: {{resolution_notes}}

If the issue returns, reply to this email within {{reopen_window}} and the ticket reopens automatically. A short satisfaction survey follows.

Nyra Service Desk', 1),
  (6, 1, 'incident.followup',           'record.followup',             'email', '[{{number}}] Still need help? (follow-up {{followup_count}} of {{followup_max}})', 'Hello {{caller_first_name}},

We have not heard back on {{number}} - {{short_description}}.

If this is resolved, no action is needed and the ticket will close after the final follow-up. If you still need help, reply to this email.

Nyra Service Desk', 1),
  (7, 1, 'incident.autoclosed',         'record.autoclosed',           'email', '[{{number}}] Closed after {{followup_max}} follow-ups with no response', 'Hello {{caller_first_name}},

{{number}} has been closed because we received no response after {{followup_max}} follow-ups.

If the issue returns, reply to this email within {{reopen_window}} and it reopens automatically.

Nyra Service Desk', 1),
  (8, 1, 'incident.sla_at_risk',        'record.sla_at_risk',          'email', '[{{number}}] SLA at risk - {{sla_remaining}} remaining', 'Action needed.

{{number}} - {{short_description}} is at risk of breaching its {{sla_target_type}} target.

Owner: {{assignee_name}}
Team: {{assignment_group}}
Due: {{sla_due}} ({{sla_percent}}% elapsed)

Open: {{record_link}}', 1),
  (9, 1, 'incident.sla_breached',       'record.sla_breached',         'email', '[{{number}}] SLA BREACHED - {{sla_target_type}}', '{{number}} has breached its {{sla_target_type}} target.

Owner: {{assignee_name}} | Team: {{assignment_group}}
Due: {{sla_due}}
Priority: {{priority_label}}

Escalate: {{record_link}}', 1),
  (10,1, 'incident.major.internal',     'record.major_incident',       'email', '[MAJOR] {{number}} - {{short_description}}', 'MAJOR INCIDENT DECLARED

{{number}} - {{short_description}}
Impact: {{impact_statement}}
Bridge: {{bridge_link}}
Incident commander: {{commander}}
Affected services: {{services}}
Next update: {{next_update_time}} (updates every {{update_interval}})

This is an internal distribution: do not forward outside the company.', 1),
  (11,1, 'incident.major.external',     'record.major_external',       'email', '[Service notice] {{service}} - disruption under investigation', 'Hello,

We are aware of a disruption affecting {{service}} in {{location}}.

What we know: {{public_summary}}
Impact: {{public_impact}}
Next update: {{next_update_time}}

We will keep you informed until the service is restored. To speak to the service desk, reply to this email.

Nyra Service Desk', 1),
  (12,1, 'record.survey',               'record.survey',               'email', '[{{number}}] How did we do?', 'Hello {{caller_first_name}},

One question, 10 seconds: how satisfied were you with the handling of {{number}}?

{{survey_links}}

Your feedback goes straight to the team that handled your ticket.', 1),
  (13,1, 'request.approval',            'approval.requested',          'email', '[Action required] Approval for {{number}}', 'Approval is required for {{number}} - {{short_description}}.

Requested by: {{requested_for}}
Cost/impact: {{cost}}
Justification: {{justification}}

Approve: {{approve_link}}
Reject: {{reject_link}}

This link works once and expires in {{expiry}}.', 1),
  (14,1, 'report.daily_digest',         'report.scheduled',            'email', '[{{group}}] Daily queue digest - {{date}}', 'Open: {{open_count}} | Unassigned: {{unassigned_count}} | At risk: {{at_risk_count}} | Breached: {{breached_count}}
Resolved yesterday: {{resolved_yesterday}} | Median resolution: {{median_resolution}}
Oldest open: {{oldest_number}} ({{oldest_age}})

Full report attached ({{report_name}}).', 1),
  (15,1, 'hr.request.created',          'record.created',              'email', '[{{number}}] HR request received - {{short_description}}', 'Hello {{caller_first_name}},

Your HR request {{number}} has been received and routed to {{assignment_group}}.

Target: {{resolve_due}}
Track: {{portal_link}}

HR Shared Services', 1)
on conflict (id) do nothing;

insert into notification_audience (id, tenant_id, code, name, audience_type, expression, expansion_mode, privacy_class) values
  (1, 1, 'caller',            'The caller on the record',        'person',           '{"kind":"record.caller"}',                     'app_expanded', 'external'),
  (2, 1, 'assignee',          'The assigned analyst',            'person',           '{"kind":"record.assignee"}',                   'app_expanded', 'internal'),
  (3, 1, 'assignment_group_dl','Assignment group distribution list','team_dl',         '{"kind":"record.assignment_group.dl"}',        'relay',        'internal'),
  (4, 1, 'assignment_group_members','Assignment group members',  'team_dl',          '{"kind":"record.assignment_group.members"}',   'app_expanded', 'internal'),
  (5, 1, 'service_owner',     'Service owner group',             'org_slice',        '{"kind":"service.owner_group"}',               'app_expanded', 'internal'),
  (6, 1, 'it_leadership',     'IT leadership distribution list', 'distribution_list','{"kind":"static","address":"it-leadership@example.com"}', 'relay', 'internal'),
  (7, 1, 'location_all_staff','All staff at the affected location','org_slice',      '{"kind":"location.all_active_people"}',        'app_expanded', 'internal'),
  (8, 1, 'department_all',    'All staff in the department',     'org_slice',        '{"kind":"department.all_active_people"}',      'app_expanded', 'internal'),
  (9, 1, 'affected_users',    'Users affected by the incident',  'org_slice',        '{"kind":"record.affected_users"}',             'app_expanded', 'external'),
  (10,1, 'security_team',     'Security operations shared mailbox','shared_mailbox',  '{"kind":"static","address":"soc@example.com"}','relay',        'restricted'),
  (11,1, 'watchlist',         'Everyone on the record watchlist','watchlist',        '{"kind":"record.watchlist"}',                  'app_expanded', 'internal'),
  (12,1, 'vip_care',          'VIP care team',                   'role',             '{"kind":"role","role":"team_lead","domain":"it"}', 'app_expanded', 'internal')
on conflict (id) do nothing;

insert into notification_send_log (id, tenant_id, record_id, template_code, template_version, audience_code, recipients_count, recipients, delivery_state, proof_class, initiated_by_type, message_id) values
  (1, 1, 2, 'incident.created', 1, 'caller', 1, '[{"person_id":21,"email":"kiran.p@example.com"}]', 'delivered', 'transactional', 'system', '<seed-1@nyra>'),
  (2, 1, 2, 'incident.assigned_group', 1, 'assignment_group_dl', 1, '[{"team_id":4,"email":"apps-l3@example.com","mode":"relay"}]', 'delivered', 'transactional', 'system', '<seed-2@nyra>'),
  (3, 1, 2, 'incident.major.internal', 1, 'it_leadership', 1, '[{"email":"it-leadership@example.com","mode":"relay"}]', 'delivered', 'regulatory_evidence', 'user', '<seed-3@nyra>'),
  (4, 1, 1, 'incident.comment_public', 1, 'caller', 1, '[{"person_id":20,"email":"meera.d@example.com"}]', 'opened', 'transactional', 'system', '<seed-4@nyra>'),
  (5, 1, 3, 'record.survey', 1, 'caller', 1, '[{"person_id":23,"email":"sam.c@example.com"}]', 'actioned', 'informational', 'system', '<seed-5@nyra>')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- saved views
insert into saved_view (id, tenant_id, name, entity, owner_id, filters, columns, shared, sort) values
  (1, 1, 'My open', 'record', 3, '{"assignee":"me","open":true}', '["number","priority","short_description","state","resolve_due_at"]', false, 'priority asc, resolve_due_at asc'),
  (2, 1, 'Unassigned L1', 'record', 2, '{"assignment_group_id":1,"assignee":null,"open":true}', '["number","priority","short_description","channel","opened_at"]', true, 'priority asc'),
  (3, 1, 'P1/P2 all teams', 'record', 1, '{"priority":[1,2],"open":true}', '["number","type","priority","assignment_group_id","assignee_id","state","resolve_due_at","sla_state"]', true, 'priority asc, resolve_due_at asc'),
  (4, 1, 'At risk / breached', 'record', 1, '{"sla_state":["at_risk","breached"]}', '["number","priority","sla_state","assignment_group_id","assignee_id","resolve_due_at"]', true, 'resolve_due_at asc'),
  (5, 1, 'Major incidents', 'record', 1, '{"major_incident":true}', '["number","short_description","state","resolve_due_at","assignee_id"]', true, 'opened_at desc'),
  (6, 1, 'HR queue', 'record', 9, '{"assignment_group_id":7,"open":true}', '["number","short_description","state","priority","opened_at"]', true, 'opened_at asc'),
  (7, 2, 'Plant critical', 'record', 40, '{"priority":[1,2],"open":true}', '["number","short_description","state","assignment_group_id","assignee_id"]', true, 'priority asc')
on conflict (id) do nothing;

-- ---------------------------------------------------------------- realign identity sequences
select setval(pg_get_serial_sequence('tenant','id'),            (select max(id) from tenant));
select setval(pg_get_serial_sequence('org_unit','id'),          (select max(id) from org_unit));
select setval(pg_get_serial_sequence('business_calendar','id'), (select max(id) from business_calendar));
select setval(pg_get_serial_sequence('team','id'),              (select max(id) from team));
select setval(pg_get_serial_sequence('team_member','id'),       (select max(id) from team_member));
select setval(pg_get_serial_sequence('person','id'),            (select max(id) from person));
select setval(pg_get_serial_sequence('sla_policy','id'),        (select max(id) from sla_policy));
select setval(pg_get_serial_sequence('taxonomy','id'),          (select max(id) from taxonomy));
select setval(pg_get_serial_sequence('service','id'),           (select max(id) from service));
select setval(pg_get_serial_sequence('ci','id'),                (select max(id) from ci));
select setval(pg_get_serial_sequence('numbering_sequence','id'),(select max(id) from numbering_sequence));
select setval(pg_get_serial_sequence('record','id'),            (select max(id) from record));
select setval(pg_get_serial_sequence('record_comment','id'),    (select max(id) from record_comment));
select setval(pg_get_serial_sequence('record_relationship','id'),(select max(id) from record_relationship));
select setval(pg_get_serial_sequence('kb_article','id'),        (select max(id) from kb_article));
select setval(pg_get_serial_sequence('kb_feedback','id'),       (select max(id) from kb_feedback));
select setval(pg_get_serial_sequence('csat_survey','id'),       (select max(id) from csat_survey));
select setval(pg_get_serial_sequence('notification_template','id'),(select max(id) from notification_template));
select setval(pg_get_serial_sequence('notification_audience','id'),(select max(id) from notification_audience));
select setval(pg_get_serial_sequence('notification_send_log','id'),(select max(id) from notification_send_log));
select setval(pg_get_serial_sequence('saved_view','id'),        (select max(id) from saved_view));

commit;
