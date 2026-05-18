-- MediFlow Athena queries
-- Use o database `mediflow_reports` e o workgroup criado no output `AthenaWorkGroupName`.

SELECT
  triagedata.triageid AS triage_id,
  triagedata.patientid AS patient_id,
  triagedata.riskscore AS risk_score,
  triagedata.urgencylevel AS urgency_level,
  from_iso8601_timestamp(triagedata.eventtimestamp) AS event_time,
  generatedat AS report_generated_at
FROM mediflow_reports.triage_reports
ORDER BY event_time DESC
LIMIT 50;

SELECT
  triagedata.urgencylevel AS urgency_level,
  count(*) AS total_triages,
  avg(triagedata.riskscore) AS avg_risk_score,
  max(triagedata.riskscore) AS max_risk_score
FROM mediflow_reports.triage_reports
GROUP BY triagedata.urgencylevel
ORDER BY max_risk_score DESC;

SELECT
  date(from_iso8601_timestamp(triagedata.eventtimestamp)) AS triage_date,
  count(*) AS total_triages,
  count_if(triagedata.urgencylevel = 'CRITICAL') AS critical_triages
FROM mediflow_reports.triage_reports
GROUP BY 1
ORDER BY 1 DESC;

