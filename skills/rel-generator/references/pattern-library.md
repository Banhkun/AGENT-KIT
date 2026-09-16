# REL Pattern Library

Curated, representative expressions distilled from a large production Redwood/UC4 Automation Engine system. Organized by task. These are real idioms — copy the shape that's closest to what you need and swap in the relevant parameter names, table names, or literal text, rather than deriving the escaping/structure from scratch.

## 1. Alert / notification subject lines

Simple concatenation of literal text with job/time parameters — the most common pattern for job-definition mail/alert subjects:

```
='ALERT - Job' + parameters.jobname + 'has failed'
='ALERT -' + parameters.name + 'Failed!! in EUP7-1101'
='Job Completed - AA_AS_NA_INTERFACE_MAIN -' + parameters.date + '-' + parameters.time
='Job FAILED - TGS -' + parameters.date + 'and' + parameters.time + 'CET'
='UC4-' + parameters.UC4_NAME + '-' + parameters.UC4_CLNT + ': Job Failure' + parameters.cur_job_nr
=parameters.NAME + '- Long Running Alert!!!'
```

Using `String.concat` instead of `+` (equivalent, sometimes preferred for long chains):
```
=String.concat('ALERT - Job ', parameters.JOBNAME, 'I has failed')
=String.concat('UC4-', parameters.UC4_NAME, '-', parameters.UC4_CLNT, ': Error: ', parameters.JPNAME)
=String.concat('EUP6,1001: Error in job ', parameters.JNAM)
```

Subjects with computed date stamps built in:
```
=String.concat(String.concat(String.concat('UC4 job error in ', parameters.JOBPLAN), ' JobplanNr='), parameters.JPNUMMER)
```

## 2. Alert / notification mail bodies

The recurring idiom: a newline-holding parameter (commonly `parameters.NL`, `parameters.NewLine`, or `parameters.CRLF`, defined elsewhere in the job definition) concatenated between literal text segments to build a multi-line message:

```
='Hello,' + parameters.NL + 'The task ' + parameters.JNAME + ' in jobplan ' + parameters.JPNAME + ' has completed successfully on ' + parameters.RUN_DATE + ' at ' + parameters.RUN_TIME + ' (CET)'

='Dear Team,' + parameters.NL + 'The job ' + parameters.JOBNAME + ' ran unsuccessfully.' + parameters.NL + 'Kindly Take actions from your end' + parameters.NL + 'Thank you'

='Dear Together,' + parameters.NL + parameters.NL + 'Daily Sales Trend AA has been successfully Completed.' + parameters.NL + parameters.NL + 'Regards,' + parameters.NL + 'UC4 Team'
```

Same pattern via `String.concat` (preferred once you have many segments — reads more clearly than a long `+` chain):
```
=String.concat('Hello,', parameters.NL, 'The task ', parameters.JNAME, ' in jobplan ', parameters.JPNAME, ' has failed on ', parameters.RUN_DATE, ' at ', parameters.RUN_TIME, ' (CET)')

=String.concat('Hello,', parameters.NL, parameters.NL, 'Contactmail distribution list missing or invalid in process flow ', getSystemId(), '/', Custom_REL_Functions.getUC4Client(jobId), '-', parameters.PFLOW, parameters.NL, 'Please correct documentation', parameters.NL, parameters.NL, 'Best regards', parameters.NL, 'ERP-Scheduling')
```

Bodies containing a literal URL or link — no special escaping needed for `https://` URLs inside a normal string:
```
='Hello All,' + parameters.NL + parameters.NL + 'Greetings!' + parameters.NL + parameters.NL + 'Please find the MEC month.year status as on curdate in the below link,' + parameters.NL + parameters.NL + 'https://example.com/some/path?form.a=1' + parameters.NL + parameters.NL + 'Thanks Regards,' + parameters.NL + parameters.NL + 'MS Team'
```

Bodies with nested conditional segments (rare, but shows the shape — building a report link that differs based on an environment check):
```
=Logic.if(parameters.RETCODE === 2, parameters.SMT_SOLUTION_GROUP, '')
```

## 3. Escaping — quotes and backslashes

**Escaping a literal single quote inside a string:** use `\'`.
```
='Hello,&NL#The task &#uc4_jobname# (&#cur_job_nr#) in jobplan &#uc4_jobplan# has failed.&NL#&NL#Regards,&NL#ERP Scheduling'
```
(Note: `&NL#`, `&#...#` here are the *target system's own* substitution tokens embedded as literal text inside the REL string — not REL syntax. This is common when the REL expression is generating text for another templating layer.)

**Escaping backslashes for a single literal backslash** (e.g., one path separator): double it.
```
='D:\\\\ftp_temp\\\\' + parameters.jobname + '.txt'
```
This resolves to the literal path `D:\ftp_temp\<jobname>.txt` — each `\\` in the expression becomes one `\` in the output.

**Escaping a UNC-style double backslash prefix** (`\\server\share`): needs *four* backslashes for the leading pair, i.e. `\\\\\\\\` for `\\`:
```
=String.concat('\\\\', parameters.NASFILER, '\\', parameters.PATH)
```
Note the asymmetry in real examples — the first segment (`\\\\`) renders as `\\` (UNC prefix), while a single interior separator is often just `\` (one backslash) because within a `String.concat(...)` **argument list** each string literal's backslash escaping is evaluated independently, and a single `\` between concat arguments already reads as one literal backslash once concatenated (Redwood's UNC-building idiom is inconsistent across real code — when unsure, test the resulting path length: 2 backslashes at the very start of the whole result = UNC share, 1 backslash for every other separator).

**Nested single-quoted strings inside a string** (e.g. building another REL-like or scripting fragment as a literal string) — escape the inner quotes:
```
='\'GET_PROCESS_LINE(&HND#, 2)\''
='\'ADD(&ERROR1#, 1)\''
```

**A caret/backtick style quote-escape sometimes seen for embedding into JSON-ish output** (site-specific convention, not core REL) — replacing a double quote with a different character to avoid breaking an outer JSON string:
```
=String.replace(parameters.Notes,'"','`"')
```

## 4. File paths and filenames with embedded date/time or parameters

```
=parameters.z_LOCAL_FOLDER +'\\' + parameters.z_LOCAL_FILE
=String.concat('D:\\ftp_temp\\', parameters.JOBNAME, '.txt')
=String.concat('\\\\', parameters.NASFILER, '\\', parameters.PATH, '\\', parameters.FILENAME)
='\\\\'+'fileserver.example.com\\Shares\\Data\\Downloads\\' +'Conf_Date2' +Time.format(Time.now(),'yyyy-MM-dd') + '.CSV'
='PTGB_' + Time.format( Time.expressionNow('truncate month'), 'yyyyMM' ) + '.CSV'
='IP10' + Time.format(Time.now(), 'YYYYMMdd')
```

Wildcard file-search patterns (for job wait-events / file search preconditions):
```
=String.concat('\\\\', parameters.NASFILER, '\\', parameters.PATH, '\\QT1ASCM_BOM_*.txt')
=str_match(parameters.LINE, '*.ok')   /* shown conceptually; real form below */
='str_match(' + parameters.LINE + ', *.ok)'
```

## 5. Date/time formatting and computed date ranges

Straightforward current-time formats:
```
=Time.format(Time.now(), 'yyyyMMdd')
=Time.format(Time.now(), 'yyyy-MM-dd')
=Time.format(Time.now(), 'HH:mm:ss')
=Time.formatNow('yyyyMMdd')
```

Relative dates via the time-expression mini-language:
```
=Time.format(Time.addDays(Time.now(), -1), 'yyyyMMdd')                          /* yesterday */
=Time.format(Time.expressionNow('subtract 1 month'), 'yyyyMM')                  /* last month, YYYYMM */
=Time.format(Time.expressionNow('subtract 1 month truncate month'), 'YYYYMMdd') /* first day of last month */
=Time.format(Time.expressionNow('truncate month subtract 1 day'), 'YYYYMMdd')   /* last day of previous month */
=Time.format(Time.expressionNow('truncate month add 1 month subtract 1 day'), 'YYYYMMdd') /* last day of current month */
```

Building a date *range* string (two computed bounds joined by ` - `):
```
='[' + Time.format(Time.expressionNow('truncate month'), 'yyyyMMdd') + ' - ' + Time.format(Time.expressionNow('truncate month add 1 month subtract 1 day'), 'yyyyMMdd') + ']'
```

Parsing a date held in a parameter and shifting it:
```
=Custom_REL_Functions.addDays(String.concat('YYYY-MM-DD:', parameters.I_DATE_CURRENT_INCLUDE), 1)
=Time.format(Time.expression(Time.parse(parameters.AKTDAT, Logic.if(String.length(parameters.AKTDAT) === 8, 'yyyyMMdd', 'yyMMdd')), 'subtract 1 month'), 'yyyyMMdd')
```
(`Custom_REL_Functions.*` here is a **site-specific helper library**, not a built-in — a common pattern in real systems is a shared REL function library wrapping recurring date math like this; if the user mentions a custom library, treat its functions as domain-specific helpers rather than trying to match them to the built-in catalog.)

## 6. Conditional / branching logic

Single condition:
```
=Logic.if(parameters.CLIENT === '016', 'LOGIN_R3_016_UC4CPIC', 'UC4CPIC')
=Logic.if(parameters.PARTN === 'DP', 'EN', '')
```

Multi-way via `Logic.case`:
```
=Logic.case(parameters.SID, 'QS0', 'QS0_V_ECOM_CUS_EXTRACTOR_AAAR_G1', 'PS0', 'PS0_V_ECOM_CUS_EXTRACTOR_AAAR_G1')
=Logic.case(parameters.PNR, 'IN20', 'EN', 'SG10', 'EN', '')
```

Nested `Logic.if` as an else-if chain (deeply nested chains like this are common for language/locale selection based on multiple partner codes — match the existing indentation-free single-line style used in the source system):
```
=Logic.if(parameters.PNR === '4320' || parameters.PNR === '4330', 'DE', Logic.if(parameters.PNR === 'E06K', 'EN', ''))
```

Combining a lookup with a fallback default:
```
=Logic.nvl(Query.getString('select Job.Status from Job where Job.JobId = ?', [parameters.PRUN], 'n'), '')
```

Boolean precondition logic (common for job chain preconditions gated on a time window):
```
=Logic.if(parameters.I_CHECK_JOBP > 0, Logic.if(getSystemId() === 'EUP6' || getSystemId() === 'EUP7', Logic.if(parameters.I_SAP_MAINTENANCE !== ' ', Logic.if(parameters.I_TIME_STAMP >= parameters.I_START_TIME, Logic.if(parameters.I_TIME_STAMP <= parameters.I_END_TIME, 1, 0), 0), 0), ''), '')
```

## 7. Table / config lookups

```
=Table.getColumnString('$.XX_XXXX_VAR_' + parameters.SID + '_FILESERVER', 'nasfiler', 'Value')
=Table.getColumnString('$.AA_XXXX_VAR_PIG_STATUS_EXTERNAL_DEPENDENCY', 'AA_PC_D_M_C4C_ACC')
=Table.lookup('SHARED_PARTITION', 'MFT_INTEGRATION_VARIABLES', 'mft_api_host', 'Value')
=Table.getColumnString(parameters.pTableName, parameters.pTableKey, 'Value')
=Table.getRow('Test_Table_REL', 'Germany')
```

System variables:
```
=Variable.getString('CPS_SYSTEM')
=Variable.getString('EMAIL_PROCESS_SERVER_DOWN_SUBJECT')
```

## 8. Job / database status queries

Querying the current status/timing of a job by id (typically a runtime job id held in a parameter):
```
=Query.getString('select Job.Status from Job where Job.JobId = ?', [parameters.RUNID], 'n')
=Query.getString('select Job.RunStart from Job where Job.JobId = ?', [parameters.RUNID], 'n')
=Query.getString('select jd.Name from Job j join JobDefinition jd on j.JobDefinition = jd.UniqueId where j.JobId = ?', [parameters.RUNID], 'n')
```

Finding an already-running instance of a job/jobplan by name, excluding terminal states — useful in preconditions that should skip scheduling if a prior run is still active:
```
=Logic.nvl(Query.getString('SELECT j.JobId FROM Job j JOIN JobDefinition jd ON j.JobDefinition = jd.UniqueId WHERE jd.Name = ? AND j.Status NOT IN (\'C\', \'E\', \'K\', \'A\', \'T\', \'j\', \'U\', \'u\') ORDER BY j.JobId ASC', [parameters.JOBNAME]), '')
```

Cross-chain job id/status lookups:
```
=JobChainParameters.getJobId('Step 1, Job 1')
=Custom_RELStartTime.averageRuntime(jobId, 30)   /* custom library wrapping average-runtime lookups */
```

## 9. Credentials and system connections

```
=Credential.getProtectedPasswordByProtocolRealUser('DEFAULT_PARTITION', 'login', 'SERVICE_NOW', 'SNOW_Client_secret')
=Logic.case(parameters.SYSTEM, 'EUT0', 'CONN_SQL_EUT0_UC4READ', 'EUT1', 'CONN_SQL_EUT1_UC4READ')
```

## 10. String parsing / extraction

Extracting a token from a delimited parameter (e.g., a job name segment after a fixed prefix length):
```
=String.substring(parameters.JPNAM, (parameters.HLEN2) - 1, ((parameters.HLEN2) - 1) + (parameters.HLEN4))
=String.indexOf(String.toLowerCase(parameters.JPNAM), String.toLowerCase('_'), 10 - 1)
```
Note the `- 1` / `+ 1` offset juggling throughout: REL string index functions are 0-based, but many site conventions track 1-based "length"/"position" parameters, so expect an explicit `-1` conversion at each boundary.

Splitting a bracketed array-looking string and grabbing an element:
```
=Array.get(String.split(String.replace(String.replace(parameters.I_ARRAY, '[', ''), ']', ''), ',', parameters.I_ARRAY.length()), 0)
```

Building an identifier by combining/truncating parts, with a length-based fallback to avoid exceeding a fixed max length (common for legacy fixed-width job/variant names):
```
=Logic.if(String.length(String.concat('UC4_', parameters.PNR, '_', parameters.PARTN)) > 14, String.concat('UC4_', parameters.PNR, parameters.PARTN), String.concat('UC4_', parameters.PNR, '_', parameters.PARTN))
```

## 11. Simple passthrough / identity expressions

Sometimes a default value expression is just forwarding an implicit object or another parameter, with no transformation:
```
=parameters.JOBNAME
=jobId
=getSystemId()
=jobDefinition
```

## 12. Recipient / distribution lists

```
=('user1@example.com;user2@example.com;distribution-list@example.com')
=String.concat(parameters.RECIPIENT1, ';', parameters.RECIPIENT3)
=Logic.if(String.indexOf(String.toLowerCase(parameters.RECEIPIENT), String.toLowerCase('@')) !== 0, '', 'scheduling-team@example.com')
```
