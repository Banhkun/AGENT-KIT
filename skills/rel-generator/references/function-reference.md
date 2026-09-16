# REL Function Reference and Implicit Objects

This is the full built-in function catalog for Redwood Expression Language (REL), plus the implicit objects available in each scripting context. Consult this file when you need an exact function signature, or need to confirm what objects are available in the context the expression will run in.

## Operators

Redwood Expression Language provides support for the basic arithmetic operators:

- `+` - addition and string concatenation
- `-` - subtraction
- `*` - multiplication
- `/` - division
- `%` - integer modulus
- `&&` - logical AND
- `||` - logical OR
- `!` - NOT

Comparison:

- `===` - equal to
- `!==` - not equal to
- `>` - greater than
- `>=` - greater than or equal
- `<` - less than
- `<=` - less than or equal

## Escape Character

`\\` - escape character, and thus must be escaped if the literal is meant to be used. A UNC path is specified as: `\\\\\\\\server\\\\share\\\\folder\\\\file`

## Builtin Constants

- `true` - true value of the boolean type.
- `false` - false value of the boolean type.

## Built in function classes

- BaseCast - Prefix: None.
- BaseString - Prefix: None.
- ModuleScriptingObject - Prefix: None.
- BaseArray - Prefix: Array
- BaseCast - Prefix: Casts
- BaseMath - Prefix: Math
- BaseRange - Prefix: Range
- BaseStringPrefix - Prefix: String
- BaseTime - Prefix: Time
- ExtendedRange - Prefix: Range
- ExtendedRepository - Prefix: Repository
- ExtendedTime - Prefix: Time
- ModuleScriptingConstraint - Prefix: Constraint
- ModuleScriptingCredential - Prefix: Credential
- ModuleScriptingEvent - Prefix: Event
- ModuleScriptingJDBC - Prefix: JDBC
- ModuleScriptingJobChainParameters - Prefix: JobChainParameters
- ModuleScriptingLogic - Prefix: Logic
- ModuleScriptingLoop - Prefix: Loop
- ModuleScriptingPLSQL - Prefix: PLSQL
- ModuleScriptingQuery - Prefix: Query
- ModuleScriptingSap - Prefix: SAP
- ModuleScriptingTable - Prefix: Table
- ModuleScriptingUserMessage - Prefix: UserMessage
- ModuleScriptingVariable - Prefix: Variable

The `current<data_type>` object designates the object you want to use with the function (i.e. dot-method call style).

## Array — Prefix: `Array`

| Function | Signature | Description |
|---|---|---|
| toStringArray | `RelObject Array.toStringArray(final Object[] values)` | Change a group of Strings to a String array. |
| toNumberArray | `RelObject Array.toNumberArray(final Object[] values)` | Create an array of BigDecimals from a group of numbers. |
| toDateTimeZoneArray | `RelObject Array.toDateTimeZoneArray(final Object[] values)` | Create an array of DateTimeZones. |
| toTimeArray | `RelObject Array.toTimeArray(final Object[] values)` | Create an array of BigDecimal from DateTime elements (epoch time). |
| toString | `String Array.toString(Object[] values, String delimiter)` | Create a String with all elements of the array, separated by delimiter. |
| toStringAffix | `String Array.toStringAffix(Object[] values, String delimiter, String prefix, String suffix)` | Create a String with all elements, separated by delimiter and surrounded by prefix/suffix. |
| get | `Object Array.get(Object[] array, int index)` | Retrieve the element from the array at index. Throws if array is null or index out of bounds. |

Examples:
- `=Array.toStringArray('Apples', 'Oranges', 'Bananas', 'Lemons')` → array with 4 elements.
- `=Array.toNumberArray(1, 2, 3, 4)` → array with 4 numbers.
- `=Array.toString(['Apples', 'Oranges', 'Bananas', 'Lemons'], ',')` → `"Apples,Oranges,Bananas,Lemons"`.
- `=Array.toStringAffix(['Apples', 'Oranges', 'Bananas', 'Lemons'], ',', '[', ']')` → `"[Apples,Oranges,Bananas,Lemons]"`.
- `=Array.get(['Apples', 'Oranges', 'Bananas', 'Lemons'], 0)` → `"Apples"`.

## Cast — Prefix: (none)

| Function | Signature | Description |
|---|---|---|
| ToBoolean | `Object ToBoolean(Object arg)` | Convert arg to boolean if possible. |
| ToNumber | `Object ToNumber(Object arg)` | Convert arg to a number if possible. |
| ToInteger | `Object ToInteger(Object arg)` | Convert arg to an integer if possible. |
| ToString | `Object ToString(Object arg)` | Convert arg to a string. |
| ToYN | `Object ToYN(Object arg)` | Convert arg to `Y` for true, `N` for any other value. |

Examples: `=ToBoolean('true')` → true. `=ToNumber('123')` → 123. `=ToInteger('123')` → 123. `=ToString(true)` → `"true"`. `=ToYN('true')` → `"Y"`.

## Math — Prefix: `Math`

| Function | Signature | Description |
|---|---|---|
| abs | `BigDecimal Math.abs(BigDecimal x)` | Absolute value. |
| floor | `BigDecimal Math.floor(BigDecimal x)` | Floor. |
| ceil | `BigDecimal Math.ceil(BigDecimal x)` | Ceiling. |
| round | `BigDecimal Math.round(BigDecimal x)` | Round (x.5 rounds up). |
| getInstance | `BaseMath Math.getInstance()` | — |

Examples: `=Math.abs(-12.12)` → 12.12. `=Math.floor(-12.12)` → -13. `=Math.ceil(-12.12)` → -12. `=Math.round(12.49)` → 12.

## Range — Prefix: `Range`

Set notation: `"XXXXXXX"` where X is `_` or a letter. First position = 0 (Sunday for days-of-week, January for months). Letters are "in the set", `_` is not.

Example sets:
| Set | X's | English |
|---|---|---|
| First month of quarter | `X__X__X__X__` | `J__A__M__O__` |
| Last month of quarter | `__X__X__X__X` | `__M__J__S__D` |
| Not last month of quarter | `XX_XX_XX_XX_` | `JF_AM_JA_ON_` |
| Mon/Wed/Fri | `_X_X_X_` | `_M_W_F_` |
| Sat/Sun | `X_____X` | `S_____S` |

Ranges: comma-separated sections, each a number (`1`) or a number range (`4-7`).

| Function | Signature | Description |
|---|---|---|
| inRange | `boolean Range.inRange(int candidate, String trueRange)` | True if candidate is in trueRange. |
| inSet | `boolean Range.inSet(int candidate, String trueSet)` | True if candidate is in trueSet. |
| inRangeWarning (Extended) | `boolean Range.inRangeWarning(int candidate, String trueRange, String warningRange, int severity, String message)` | True if candidate in trueRange; also logs a warning operator message if candidate is in warningRange. |

Examples:
- `=Range.inRange(Time.format(Time.now('Europe/Berlin'), 'd'), '1-7')` — true if day-of-month is 1-7.
- `=Range.inSet(Time.format(Time.now('Europe/Berlin'), 'M'), ' X__X__X__X__')` — true if current month is first month of a quarter (leading space converts 1-based month to 0-based set).
- `=Range.inRangeWarning(52, '10-50', '51-100', 50, 'Warning: range exceeded')` → true, and creates an operator message.

## String (dot-method style) — Prefix: (none)

Call as `currentString.method(...)`.

| Function | Signature | Description |
|---|---|---|
| concat | `String currentString.concat(String s1, ...)` | Concatenate strings. |
| toString | `String currentString.toString()` | Convert to string. |
| charAt | `String currentString.charAt(int pos)` | Character at pos (0-based). |
| indexOf | `int currentString.indexOf(String searchFor, [int startIndex])` | First index of searchFor. |
| lastIndexOf | `int currentString.lastIndexOf(String searchFor, [int endIndex])` | Last index of searchFor. |
| replace | `String replace(String search, String replaceBy)` | Replace search with replaceBy. |
| split | `String[] currentString.split(String separator, int limit)` | Split into array, limited to `limit` elements. |
| substring | `String currentString.substring([int startIndex] [, int endIndex])` | Substring [startIndex, endIndex). If endIndex omitted, returns rest of string. |
| toLowerCase | `String currentString.toLowerCase()` | Lowercase. |
| toUpperCase | `String currentString.toUpperCase()` | Uppercase. |
| length | `int currentString.length()` | Length. |
| getSystemId | `String getSystemId()` | Current system id. |
| contains | `boolean currentString.contains(Object[] args)` | Contains searchFor. |
| startsWith | `boolean currentString.startsWith(Object[] args)` | Starts with searchFor. |
| trim | `String currentString.trim(Object[] args)` | Trim leading/trailing whitespace. |

Examples:
- `='Hello'.concat(' World', '!')` → `"Hello World!"`.
- `='123'.toString()` → `"123"` (as a string).
- `='Hello World!'.charAt(4)` → `"o"`.
- `='Hello World!'.indexOf('o')` → 4; `.indexOf('o', 5)` → 7.
- `='Hello World!'.lastIndexOf('o')` → 7; `.lastIndexOf('o', 5)` → 4.
- `='abc def ghi'.replace('def', '123')` → `"abc 123 ghi"`.
- `='1 2 3 4 5 6 7 8 9 10'.split(' ', 5)` → `[1, 2, 3, 4, 5]`.
- `='Hello World!'.substring(0)` → `"Hello World!"`; `.substring(6)` → `"World!"`; `.substring(1, 3)` → `"el"`.
- `='HeLLo WorLd!'.toLowerCase()` → `"hello world!"`; `.toUpperCase()` → `"HELLO WORLD!"`.
- `='HeLLo WorLd!'.length()` → 12.
- `=getSystemId()` → e.g. `redwood-university_test`.
- `='Hello'.contains('l')` → true; `.contains('lol')` → false.
- `='Hello'.startsWith('He')` → true; `.startsWith('llo')` → false.
- `='Hello '.trim()`, `=' Hello'.trim()`, `=' Hello '.trim()` → `"Hello"`. `='Hel lo'.trim()` → `"Hel lo"` (internal space preserved).

## String — Prefix: `String`

Call as `String.method(instance, ...)`. Same functions as above, static style — preferred when composing nested calls.

| Function | Signature |
|---|---|
| concat | `String String.concat(String instance, [String s1,] ...)` |
| toString | `String String.toString(String instance)` |
| charAt | `String String.charAt(String instance, int pos)` |
| indexOf | `int String.indexOf(String instance, String searchFor, [int startIndex])` |
| lastIndexOf | `int String.lastIndexOf(String instance, String searchFor, [int startIndex])` |
| replace | `String String.replace(String input, String search, String replaceBy)` |
| split | `String[] String.split(String instance, String separator, int limit)` |
| substring | `String String.substring(String instance, [int startIndex] [, int endIndex])` |
| toLowerCase | `String String.toLowerCase(String instance)` |
| toUpperCase | `String String.toUpperCase(String instance)` |
| length | `int String.length(String instance)` |
| getSystemId | `String String.getSystemId()` |
| contains | `boolean String.contains(String instance, String searchFor)` |
| startsWith | `boolean String.startsWith(String instance, String searchFor)` |
| trim | `String String.trim(String instance)` |

Examples:
- `=String.concat(Time.now('Europe/Paris'), ', Rue Toulouse-Lautrec')`
- `=String.toString(123)` → `"123"`.
- `=String.charAt('Hello John', 4)` → `"o"`.
- `=String.indexOf('Hello', 'l', '3')` → 3.
- `=String.lastIndexOf('Hello', 'l', '3')` → 3.
- `=String.replace('abc def ghi', 'def', '123')` → `"abc 123 ghi"`.
- `=String.split('Some people like', ' ', '3')` → `["Some", "people", "like"]`.
- `=String.substring('like it on ice', 8, 14)` → `"on ice"`.
- `=String.toLowerCase('but I like it dry.')`, `=String.toUpperCase('I like it dry.')`.
- `=String.length('but I like it dry.')` → 18.
- `=String.getSystemId()`.
- `=String.contains('Hello', 'l')` → true.
- `=String.startsWith('Hello', 'He')` → true.
- `=String.trim(' Hello ')` → `"Hello"`.

## Time — Prefix: `Time`

Time expressions are a sequence of operations applied in order to a time (usually now, or a specified date):

- `set <specifier> <value>` — set specifier to value
- `add <value> <specifier>` — add value to specifier (may propagate)
- `subtract <value> <specifier>` — subtract value from specifier (may propagate)
- `truncate <specifier>` — zero everything below specifier

`<value>` is always a number. Days-of-week start at 1 for Sunday; days-of-year start at 1 for Jan 1.

`<specifier>`:
- add/subtract: `second, minute, hour, day, week, month, year`
- truncate: `second, minute, hour, day, month`
- set: `second, minute, hour, day, day_of_week, day_of_year, week_of_month, month`

Plurals with trailing 's' accepted (`days`, `weeks`, ...). English day/month names accepted for `set day_of_week` / `set month` (3-letter abbreviations OK too).

Examples of the mini-language: `add 1 minute`, `add 3 seconds`, `set hour 1`, `set day_of_week Mon`, `truncate day`, `subtract 2 days`.

Default time zone is the JVM time zone unless overridden with an Olson name.

| Function | Signature | Description |
|---|---|---|
| now | `DateTimeZone Time.now([String timeZoneName])` | Time in context time zone (or specified Olson zone). |
| expression | `DateTimeZone Time.expression(Object date, String expression)` | Apply time expression to date (returns new object). |
| expressionNow | `DateTimeZone Time.expressionNow(String expression)` | Apply time expression to current time. |
| isTimeWindowOpenNow | `boolean Time.isTimeWindowOpenNow(String timeWindow)` | Is the named time window open now. |
| isTimeWindowOpen | `boolean Time.isTimeWindowOpen(Object date, String timeWindow)` | Is the time window open on the specified date. `$` may be used as partition placeholder. |

Examples:
- `=Time.now()` → current time with time zone.
- `=Time.expression(Time.now('Europe/Amsterdam'), 'add 1 day')` → tomorrow, Amsterdam time.
- `=Time.expressionNow('truncate day')` → today at midnight.
- `=Time.isTimeWindowOpenNow('GLOBAL.System_Week_Monday')` → true if today is Monday.
- `=Time.isTimeWindowOpen(Time.expressionNow('subtract 1 day'), 'GLOBAL.System_Week_Monday')` → true if today is Tuesday.
- `=Time.isTimeWindowOpen(Time.expressionNow('truncate day add 3 hours add 25 minutes'), '$.SomeTimeWindow')` — `$` = partition of the current job definition/chain.

## Time — Extended, Prefix: `Time`

Legacy `sysdate`/`systimestamp` equivalents:
- sysdate → `=Time.format(Time.now(), 'dd-MM-yyyy')`
- systimestamp → `=Time.format(Time.now(), 'dd-MM-yyyy hh.mm.ss.SSS a XXXXX')`

| Function | Signature | Description |
|---|---|---|
| isDayOfWeekInSetNow | `boolean Time.isDayOfWeekInSetNow(String weekSet)` | Current day-of-week in weekSet? |
| isDayOfWeekInSet | `boolean Time.isDayOfWeekInSet(Object date, String weekSet)` | Day-of-week of date in weekSet? |
| isDayInRangeNow | `boolean Time.isDayInRangeNow(String dayRange)` | Current day-of-month in dayRange? |
| isDayInRange | `boolean Time.isDayInRange(Object date, String dayRange)` | Day-of-month of date in dayRange? |
| isLastDayInMonthNow | `boolean Time.isLastDayInMonthNow()` | Is today last day of month? |
| isLastDayInMonth | `boolean Time.isLastDayInMonth(Object date)` | Is date the last day of its month? |
| isMonthInSetNow | `boolean Time.isMonthInSetNow(String monthSet)` | Current month in monthSet? |
| isMonthInSet | `boolean Time.isMonthInSet(Object date, String monthSet)` | Month of date in monthSet? |
| format | `String Time.format(Object date, String format)` | Format date with SimpleDateFormat pattern, default locale. |
| formatLocale | `String Time.formatLocale(Object date, String format, String localeName)` | Format with pattern + locale (`language[_country[_variant]]`). |
| formatDuration | `String Time.formatDuration(BigDecimal duration)` | Format a millisecond duration with standard format. |
| formatDurationEx | `String Time.formatDurationEx(BigDecimal duration, String format)` | Format duration with custom template (`\|1 week, \|# weeks, \|1 day, \|# days, \|#\|:#\|:#\|.#\|`). |
| getUTCMillisecondsNow | `BigDecimal Time.getUTCMillisecondsNow()` | Milliseconds since epoch, now. |
| getUTCMilliseconds | `BigDecimal Time.getUTCMilliseconds(Object date)` | Milliseconds since epoch for date. |
| formatNow | `String Time.formatNow(String format)` | Format current date. |
| parse | `DateTimeZone Time.parse(Object string, String format)` | Parse string into date per format. |
| nextTimeWindowOpeningNow | `DateTimeZone Time.nextTimeWindowOpeningNow(String timeWindow)` | Next opening of timeWindow after now. |
| nextTimeWindowOpening | `DateTimeZone Time.nextTimeWindowOpening(Object date, String timeWindow)` | Next opening after date. |
| nextTimeWindowClosingNow | `DateTimeZone Time.nextTimeWindowClosingNow(String timeWindow)` | Next closing after now. |
| nextTimeWindowClosing | `DateTimeZone Time.nextTimeWindowClosing(Object date, String timeWindow)` | Next closing after date (only for currently-open windows). |
| addOpenDays | `DateTimeZone Time.addOpenDays(Object date, String timeWindow, int days)` | Add days to date per time window. |
| addOpenDaysFromNow | `DateTimeZone Time.addOpenDaysFromNow(String timeWindow, int days)` | Add days to current date per time window. |

Examples:
- `=Time.isDayOfWeekInSetNow('_X_X_X_')` → true if Mon/Wed/Fri.
- `=Time.isDayInRangeNow('4-7')` → true if day-of-month is 4-7.
- `=Time.isLastDayInMonthNow()`
- `=Time.isMonthInSetNow('_X_X_X_X_X_X')` → true if current month is even.
- `=Time.format(Time.now(), 'yyyy-MM-dd')` → `"2025-08-14"`.
- `=Time.formatLocale(Time.now(), 'yyyy-MM-dd', 'de_DE')`
- `=Time.formatDuration(100000)` → `"0:01:40.000"`.
- `=Time.formatNow('yyyyMMddhhmmss')` → `"20251031125200"`.
- `=Time.parse('20251031125200', 'yyyyMMddhhmmss')`
- `=Time.nextTimeWindowOpeningNow('GLOBAL.System_Week_Thursday')`
- `=Time.addOpenDaysFromNow('System_Week_WorkDays', 10)`

## Constraint — Prefix: `Constraint`

Used in the "Simple Constraint Data" field (constraint type = Expression).

| Function | Signature | Description |
|---|---|---|
| listConstraint | `boolean Constraint.listConstraint(Object[] args /*String title, String list[, boolean valid[, String separator]]*/)` | Dropdown with a list of values. `list` is comma-separated values (or split by custom `separator`). `valid` is a boolean expression using implicit `value`; if omitted, only listed values are allowed. |
| pairListConstraint | `boolean Constraint.pairListConstraint(Object[] args /*String titles, String list[, boolean valid]*/)` | Dropdown of value=description pairs; `titles` is a comma-separated pair of column titles. |

Examples:
- `=Constraint.listConstraint('Country', 'de,nl,gt', value !== '')` — dropdown of de/nl/gt but any non-empty value allowed.
- `=Constraint.listConstraint('Country', 'de,nl,gt')` — dropdown, restricted to listed values only.
- `=Constraint.listConstraint('Ciphers or letters', '1,2,3,...|a,b,c,...', null, '\\|')` — custom `|` separator (escaped as regex).
- `=Constraint.pairListConstraint('Country, Code', 'de=49,nl=31,gt=502', value !== '')`
- `=Constraint.pairListConstraint('Code|Various symbols', 'C:1,2,3,...|L:a,b,c,...|O:=-*+/', null, '\\|', ':')` — custom pair-separator (`:`) and list-separator (`|`).

## Credential — Prefix: `Credential`

| Function | Signature | Description |
|---|---|---|
| getProtectedPasswordByProtocolRealUser | `String Credential.getProtectedPasswordByProtocolRealUser(String partition, String credentialProtocol, String endpoint, String realUser)` | Obtain encrypted credential. |
| getProtectedPasswordByProtocolVirtualUser | `String Credential.getProtectedPasswordByProtocolVirtualUser(String partition, String credentialProtocol, String endpoint, String virtualUser)` | Obtain encrypted credential for a virtual user. |
| getProtectedPassword | `String Credential.getProtectedPassword(String endpoint, String realUser)` | Obtain encrypted credential for default partition/protocol. |

Examples:
- `=Credential.getProtectedPasswordByProtocolRealUser('GLOBAL', 'login', 'host', 'root')` or `=Credential.getProtectedPasswordByProtocolRealUser('$', 'login', 'host', 'root')` (`$` = partition of current object).
- `=Credential.getProtectedPasswordByProtocolVirtualUser('GLOBAL', 'login', 'host', 'appowner')`
- `=Credential.getProtectedPassword('host', 'root')`

## Event — Prefix: `Event`

| Function | Signature | Description |
|---|---|---|
| isEventRaised | `boolean Event.isEventRaised(String name)` | Status of an event. |

Example: `=Event.isEventRaised('MyPartition.MyEvent')`

## JDBC — Prefix: `JDBC`

| Function | Signature | Description |
|---|---|---|
| clearCache | `String JDBC.clearCache()` | Clears result cache; returns empty string. |
| constraint | `Object JDBC.constraint(Object[] args)` | Constraint with LOV support based on a DB query. First param: connection info string `[user=<user>] [endpoint=<endpoint>] [cache=[<n>[s\|m\|h\|d\|w\|M\|y]]]`. Second param: query with `?` bind placeholders. Rest: bind values. |
| query | `Object JDBC.query(Object[] args)` | Execute a query, return first column of first row. Same param shape as `constraint`. |

Cache spec: number = seconds by default, or suffixed `s/m/h/d/w/M/y`. The cache max-age is defined by the *getter*, not the setter.

Examples:
- `=JDBC.constraint('user=scott endpoint=xe', 'select name "City", state "State/province" from cities where country = ?', parameters.Country)`
- `=JDBC.query('user=scott endpoint=xe', 'select global_name from global_name where rownum <= ?', 1)` — no cache.
- `=JDBC.query('user=scott endpoint=xe cache=60', 'select global_name from global_name where rownum <= ?', 1)` — cached up to 60s.
- `=JDBC.query('user=scott endpoint=xe cache=1m', ...)` — cached up to 1 minute.

## JobChainParameters — Prefix: `JobChainParameters`

Job chain job names take the form `Step name, job job number` (e.g. `Step 2, job 3`), 1-based (first job is `Job 1`). **Caution:** if a job is deleted from a step, later jobs keep their original number — always re-verify these expressions after editing a chain.

| Function | Signature | Description |
|---|---|---|
| getOutValueString | `String JobChainParameters.getOutValueString(String jobName, String parameterName)` | String Out value of parameterName on jobName in current chain. |
| getOutValueNumber | `BigDecimal JobChainParameters.getOutValueNumber(String jobName, String parameterName)` | Number Out value. |
| getOutValueDate | `DateTimeZone JobChainParameters.getOutValueDate(String jobName, String parameterName)` | Date Out value. |
| getOutValueArray | `Object[] JobChainParameters.getOutValueArray(String jobName, String parameterName)` | Array Out value. |
| getInValueString | `String JobChainParameters.getInValueString(String jobName, String parameterName)` | String In value. |
| getInValueNumber | `BigDecimal JobChainParameters.getInValueNumber(String jobName, String parameterName)` | Number In value. |
| getInValueDate | `DateTimeZone JobChainParameters.getInValueDate(String jobName, String parameterName)` | Date In value. |
| getInValueArray | `Object[] JobChainParameters.getInValueArray(String jobName, String parameterName)` | Array In value. |
| getJobId | `Long JobChainParameters.getJobId(String jobName)` | Job id of jobName. |
| getJobStatus | `String JobChainParameters.getJobStatus(String jobName)` | Job status of jobName. |
| getJobReturnCode | `Long JobChainParameters.getJobReturnCode(String jobName)` | Return code of jobName. |
| getJobFilePath | `String JobChainParameters.getJobFilePath(String jobName, String jobFileName)` | Full path of short-named job file. |
| jobFileExists | `boolean JobChainParameters.jobFileExists(String jobName, String jobFileName)` | Whether that job file exists and is readable. |

Examples:
- `=JobChainParameters.getOutValueString('Step 1, Job 1', 'Parameter')`
- `=JobChainParameters.getJobId('Step 1, Job 1')`
- `=JobChainParameters.getJobStatus('Step 2, Job 1')`
- `=JobChainParameters.getJobFilePath('Step 1, Job 1', 'stdout.log')`
- `=JobChainParameters.jobFileExists('Step 1, Job 1', 'stdout.log')`

## Logic — Prefix: `Logic`

| Function | Signature | Description |
|---|---|---|
| case | `String Logic.case(String expression[, String match1, String result1,] ... [String matchN, String resultN] [, String resultNoMatch])` | Evaluate expression; if it matches matchN return resultN, else resultNoMatch. |
| if | `String Logic.if(String expression, String trueValue, String falseValue)` | Ternary. No native "else if" — chain `Logic.if(...)` calls, or use `Logic.case`. |
| nvl | `String Logic.nvl(String o, String nullValue)` | Return o if not null, else nullValue. |

Examples:
- `=Logic.case(getSystemId(), 'redwood-university_test', 'test', 'redwood-university_prod', 'prod', 'Not Matched')`
- `=Logic.if(getSystemId() === 'redwood-university_test', 'test', 'Not Matched')`
- `=Logic.nvl(getSystemId(), 'Not null')`

## Loop — Prefix: `Loop`

Used inside report/loop row-iteration contexts to read the current row's columns.

| Function | Signature | Description |
|---|---|---|
| getString | `String Loop.getString(String columnName)` | String value of column. |
| getBigDecimal | `BigDecimal Loop.getBigDecimal(String columnName)` | Numeric value of column. |
| getDate | `DateTimeZone Loop.getDate(String columnName)` | Date value of column. |
| formatBigDecimal | `String Loop.formatBigDecimal(String columnName, String outputFormat)` | Format a numeric-parseable column. |
| formatDate | `String Loop.formatDate(String columnName, String dateFormat)` | Format a date-parseable column. |
| reformatStringAsBigDecimal | `String Loop.reformatStringAsBigDecimal(String columnName, String inputFormat, String outputFormat)` | Parse then reformat a numeric string column. |
| reformatStringAsDate | `String Loop.reformatStringAsDate(String columnName, String inputFormat, String outputFormat)` | Parse then reformat a date string column. |

Examples:
- `=Loop.getString('symbol')`
- `=Loop.getBigDecimal('price')`
- `=Loop.formatBigDecimal('price', '$#.00')`
- `=Loop.formatDate('date', 'dd-MM-yyyy')`
- `=Loop.reformatStringAsBigDecimal('price', '$#.00', '#,00')`
- `=Loop.reformatStringAsDate('date', 'yyyy-MM-dd', 'dd-MM-yyyy')`

## Object — Prefix: (none)

| Function | Signature | Description |
|---|---|---|
| getMember | `Object getMember(final Object[] args)` | Get a member value from a ScriptObject if it exists (throws NoSuchIdentifierException otherwise). |

Example: `=columns.getMember('Price in EUR')`

## PLSQL — Prefix: `PLSQL`

Evaluate PL/SQL expressions in an Oracle database. Connection info string and cache semantics match `JDBC`.

| Function | Signature | Description |
|---|---|---|
| booleanExpr | `Boolean PLSQL.booleanExpr(Object[] args)` | Evaluate boolean PL/SQL expr. First param: connection info. Second: expression. Rest: bind values (`?` placeholders). |
| dateExpr | `DateTimeZone PLSQL.dateExpr(Object[] args)` | Same, returns date. |
| numberExpr | `BigDecimal PLSQL.numberExpr(Object[] args)` | Same, returns number. |
| stringExpr | `String PLSQL.stringExpr(Object[] args)` | Same, returns string. |

Examples:
- `=PLSQL.booleanExpr('user=scott endpoint=xe', '? > 0', 1)`
- `=PLSQL.booleanExpr('user=scott endpoint=xe cache=1m', '? > 0', 1)`
- `=PLSQL.booleanExpr('user=scott cache=1m', '? > ?', parameters.param1, parameters.param2)` — omitting endpoint uses the default `System_Oracle` endpoint.

## Query — Prefix: `Query`

| Function | Signature | Description |
|---|---|---|
| getNumber | `BigDecimal Query.getNumber(String query [, Object[] bindVariables [, String bindTypes]])` | First column of first row, as number. |
| getString | `String Query.getString(String query [, Object[] bindVariables [, String bindTypes]])` | First column of first row, as string. |
| getRelativeJob | `BigDecimal Query.getRelativeJob(String jobName)` | Job id of jobName in current chain (1-based; note the chain editor UI is 0-based, so `Step 1, Job 1` shows as `Step 1, Job 0` there). |

`bindTypes`: for each bind variable, `"s"` (string) or `"n"` (number); unspecified defaults to string. Needed on databases that don't auto-convert.

Examples:
- `=Query.getNumber('select Job.JobId from Job where Job.Description=\'My Job\'')`
- `=Query.getNumber('select Job.ReturnCode from Job where Job.JobId = ?', [JobChainParameters.getJobId('Step 1,job 1')], 'n')`
- `=Query.getString('select Job.Description from Job where Job.Queue in (select q.UniqueId from Queue q where q.Name=?) order by Job.JobId DESC', ['System'])`
- `=Query.getString('select Job.Description from Job where Job.JobId=?', [parameters.JOBID], 'n')` — cast needed when the parameter is a String type holding a numeric job id.
- `=Query.getRelativeJob('Step 1, Job 1')`

## SAP — Prefix: `SAP`

Ranges are sent as `[<sign><option><low><high>]+` where `<sign>` is `I`/`E`, `<option>` is a select option (`EQ`, `BT`, ...), fields are blank-padded to length. (Known to be produced by Closing Cockpit.)

| Function | Signature | Description |
|---|---|---|
| convertJobParameterRangesToExpression | `String SAP.convertJobParameterRangesToExpression(String jobName, String parameterName, int fieldLength)` | Convert a job's Out parameter range string to a selopt expression. |
| convertRangesToExpression | `String SAP.convertRangesToExpression(String rangesString, int fieldLength)` | Convert a ranges string to a selopt expression. |

Example: `=SAP.convertRangesToExpression('IBTAAZZ', 2)` → `"AA - ZZ"`.

## Table — Prefix: `Table`

Use `$` to denote the partition of the object being edited.

| Function | Signature | Description |
|---|---|---|
| getRow | `String Table.getRow(String table, String key)` | Row of a table, all values concatenated. |
| getColumnString | `String Table.getColumnString(String tableName, String key, String column)` | String value from a table. |
| getColumnNumber | `BigDecimal Table.getColumnNumber(String table, String key, String column)` | Number value from a table. |
| formatRow | `String Table.formatRow(String table, String key, String rowStart, String columnFormat, String columnSeparator, String rowEnd)` | Retrieve and format a row. `columnFormat` supports `{0}`=header, `{1}`=value, `{2}`=columnSeparator. |
| l | `String Table.l(Object[] parameters /*partitionName, tableName, key, columnName*/)` | Shorthand for `lookup`. |
| lookup | `String Table.lookup(Object[] parameters /*partitionName, tableName, key, columnName*/)` | Value of a column for a row in a table; if no partition given, looks in GLOBAL. |

Examples:
- `=Table.getRow('System_Variables', 2)`
- `=Table.getColumnString('System_Variables', '2', 'SystemValue')`
- `=Table.getColumnNumber('System_Variables', 'CCOP')`
- `=Table.formatRow('System_Variables', 2, '<row><entry>', '{1}', '</entry><entry>', '</entry></row>')`
- `=Table.formatRow('$.Countries', 49, '#', '{2}{0}={1}', '|', '#')`
- `=Table.lookup('PROD', 'CustomTable', 'Identifier10', 'ColumnA')` — table `CustomTable` in partition `PROD`.
- `=Table.lookup('CustomTable', 'Identifier10', 'ColumnA')` — table in GLOBAL partition (partitionName omitted).

## UserMessage — Prefix: `UserMessage`

| Function | Signature | Description |
|---|---|---|
| renderHistoryAsHTML | `String UserMessage.renderHistoryAsHTML(String userMessageId, String cssPrefix)` | HTML table of a user message's history. |
| renderHistoryAsText | `String UserMessage.renderHistoryAsText(String userMessageId)` | Text table of a user message's history. |

Examples:
- `=UserMessage.renderHistoryAsHTML(parameters.UserMessage_UniqueId, 'aCssPrefix')`
- `=UserMessage.renderHistoryAsText(parameters.UserMessage_UniqueId)`

## Variable — Prefix: `Variable`

Queries the `System_Variables` table.

| Function | Signature | Description |
|---|---|---|
| getString | `String Variable.getString(String key)` | String value from System_Variables. |
| getNumber | `BigDecimal Variable.getNumber(String key)` | Number value from System_Variables. |

Examples: `=Variable.getString('2')`, `=Variable.getNumber('CCOP')`

## Repository — Extended, Prefix: `Repository`

| Function | Signature | Description |
|---|---|---|
| getSystemId | `String Repository.getSystemId()` | Current system id. |
| getParentJobId | `String Repository.getParentJobId(String jobId)` | Parent job id of jobId (null if none). |
| queryHTMLTable | `int Repository.queryHTMLTable(String query [, Object[] bindVariables])` | Produce HTML output for a query on stdout. |
| queryCSV | `int Repository.queryCSV(String query [, Object[] bindVariables])` | Produce CSV output for a query on stdout. |

Examples:
- `=Repository.getSystemId()`
- `=Repository.getParentJobId('27')`
- `=Repository.queryHTMLTable('select Job.Description from Job where Job.JobId = 21')`
- `=Repository.queryCSV('select Job.Description from Job where Job.JobId = 21')`

---

# Scripting Contexts and Implicit Objects

REL can be used to specify: job definition parameter default values, job definition return code mappings, job chain step preconditions, job chain job preconditions, job chain job parameter mappings, job chain job scheduling parameters, event raiser comments, and more. Each context makes a different set of implicit objects available — **always check this table before referencing an object**, since using one out of scope for the context will fail.

## Generic implicit objects (available broadly, context-dependent)

| Implicit object | Description | Class |
|---|---|---|
| `parameters.<name>` | Value of parameter `<name>` of current job. | Character, String, Number, Date, Time, DateTimeZone, Table, FileParameter |
| `outParameters.<name>` | Value of Out parameter `<name>` of current job. | same as above |
| `chainParameters.<name>` | Value of parameter `<name>` of inner-most job chain. | same as above |
| `chainOutParameters.<name>` | Value of out parameter `<name>` of inner-most job chain. | same as above |
| `JobChainParameters.getOutValueString(<jobName>, <parameter>)` | Out parameter value of the named job in chain. | String |
| `JobChainParameters.getOutValueNumber(<jobName>, <parameter>)` | Same, Number. | Number |
| `JobChainParameters.getOutValueDate(<jobName>, <parameter>)` | Same, Date. | Date |
| `chainJobId` | Job id of the inner-most chain (needs to be a runtime parameter). | Number |
| `jobId` | Job id of the current job (needs to be a runtime parameter). | Number |
| `topLevelJobId` | Job id of highest parent job in hierarchy (needs to be a runtime parameter). | Number |
| `returnCode` | Return code of current job. | Number |
| `stepIterations` | Iteration number of the current step or job. | Number |
| `waitEvents.<name>.finalPath` | Path of the file that raised event `<name>` (after move, if applicable). | String |
| `waitEvents.<name>.originalPath` | Path of the file that raised event `<name>` (before move, if applicable). | String |
| `waitEvents.<name>.raiserComment` | Comment of the raiser for event `<name>`. | String |
| `waitEvents.<name>.raiserJobId` | Job id of the job that raised event `<name>`. | Long |
| `$.name` | Partition of the object named `name`; `$` is filled with the partition of the job definition/chain where specified. | String |

`JobChainParameters.getOutValue*` placeholders: `<jobName>` — e.g. `Step 1, Job 2` or `Extract data, Job 4`; `<parameter>` — the parameter name. Example: `=JobChainParameters.getOutValueString('Extract data, Job 4', 'Param1')`.

### The `$` partition placeholder

`$` is replaced with the partition of the job definition/job chain it's specified on. This lets an expression like `$.TW_DailyWorkShift` safely refer to a same-partition object even after promotion to another system — **but** if a job chain in a *different* partition overrides a parameter using `$.X` syntax, `$` resolves to *that chain's* partition, not the original job definition's partition. Keep objects that reference each other via `$` in the same partition/application. Note: the promotion module does **not** detect `$`-syntax references, so "export/promote with related objects" won't pick them up automatically.

### Substitution parameters (Ant-style `${...}`) vs REL

Fields that support REL also often support Ant-style `${var}` substitution inside string literals. **Ant substitution happens *after* REL evaluation** — REL only ever sees the literal substitution parameter names, not their values, so you cannot manipulate a `${var}`'s value using REL string functions. Example:

```
='Process Server ${processServer} went from ${oldStatus} to ${newStatus} at ' + Time.now()
```
evaluates as REL first (leaving the `${...}` tokens untouched), then Ant substitution fills them in. Prefer resolving values purely in REL when possible:
```
='Process Server '+processServer+' went from '+oldStatus+' to '+newStatus+' at ' + Time.now()
```
Because substitution is post-REL, `=String.substring('${processServer}', 5)` will **not** return the substituted value — it operates on the literal token text.

## Per-context implicit objects

**AdHocAlertSource**: `alertSourceType` (String), `alertSourceUniqueId` (String), `chainJobId` (String), `chainQueue` (String), `data` (String — data of the current job/process-server check), `jobDefinition` (String), `jobDescription` (String), `jobId` (Number), `parentJobId` (Number), `partition` (String), `queue` (String), `topLevelJobId` (String), `topLevelQueue` (String).

**CallSchedulingParameter**: `$` (String), `chainJobId` (String), `chainOutParameters`/`chainOutParameters.name`, `chainParameters`/`chainParameters.name`, `chainQueue` (String), `chainRequestedStartTime` (DateTimeZone), `chainRunStartTime` (DateTimeZone), `jobId` (Number), `parameters`/`parameters.name`, `parentJobId` (Number), `queue` (String), `stepIterations` (Number), `topLevelJobId` (String), `topLevelQueue` (String).

**ConstraintLOV**: `$` (String), `parameters`/`parameters.name`, `value` (Object — the value of the parameter or process server check result being validated).

**DefaultParameter** (job definition parameter default expressions): `$` (String), `jobDefinition` (String), `jobId` (Number), `parameters`/`parameters.name`, `parentJobId` (Number), `queue` (String), `username` (String), `waitEvents`/`waitEvents.name.finalPath`/`.originalPath`/`.raiserComment`/`.raiserJobId`.

**ForecastCallPrecondition**: `chainJobId`, `chainOutParameters`/`.name`, `chainParameters`/`.name`, `chainQueue`, `jobId`, `now` (Long — override for current time, UTC ms), `parameters`/`.name`, `parentJobId`, `queue`, `stepIterations`, `topLevelJobId`, `topLevelQueue`.

**ForecastStepPrecondition**: `chainJobId`, `chainOutParameters`/`.name`, `chainParameters`/`.name`, `chainQueue`, `jobId`, `now` (Long), `parentJobId`, `queue`, `stepIterations`, `topLevelJobId`, `topLevelQueue`. (No `parameters` here — forecast step preconditions run before the job's own parameters exist.)

**GotoStepEvaluation**: `jcsJob` (Job object for current job), `jobId`, `outParameters`/`outParameters.name`, `parameters`/`parameters.name`, `parentJobId`, `userMessage` (MapScriptObject — user message response instance values).

**JobChainCallPrecondition**: `$`, `callJobId` (String), `callUniqueId` (String), `chainJobId`, `chainOutParameters`/`.name`, `chainParameters`/`.name`, `chainQueue`, `jobId`, `parameters`/`.name`, `parentJobId`, `queue`, `stepIterations`, `stepJobId` (String), `stepUniqueId` (String), `topLevelJobId`, `topLevelQueue`.

**JobChainInExpression** (parameter mappings *into* a job chain job): `$`, `chainJobId`, `chainOutParameters`/`.name`, `chainParameters`/`.name`, `chainQueue`, `jobId`, `parameters`/`.name`, `parentJobId`, `queue`, `stepIterations`, `topLevelJobId`, `topLevelQueue`.

**JobChainStepPrecondition**: `chainJobId`, `chainOutParameters`/`.name`, `chainParameters`/`.name`, `chainQueue`, `jobId`, `parentJobId`, `queue`, `stepIterations`, `stepJobId`, `stepUniqueId`, `topLevelJobId`, `topLevelQueue`. (No `parameters` — evaluated before the step's job parameters exist.)

**JobDefinitionAlertSource**: `alertSourceType`, `alertSourceUniqueId`, `chainJobId`, `chainQueue`, `jobDefinition`, `jobDefinitionOwner` (String), `jobDescription`, `jobId`, `jobOwner` (String), `newStatus` (String), `oldStatus` (String), `outParameters`/`outParameters.name`, `parameters`/`parameters.name`, `parentJobId`, `partition`, `queue`, `remoteStatus` (String — status of the remote service), `returnCode`, `topLevelJobId`, `topLevelQueue`.

**JobDefinitionRuntimeLimit**: `averageRuntime` (Number), `jobId`, `parameters`/`parameters.name`, `requestedStartTime` (DateTimeZone), `scheduledStartTime` (DateTimeZone), `standardDeviationRuntime` (Number), `topLevelAgerageRuntime` (Number — note: this is the actual (misspelled) field name in the product), `topLevelJobId`, `topLevelRequestedStartTime` (DateTimeZone), `topLevelScheduledStartTime` (DateTimeZone), `topLevelStandardDeviationRuntime` (Number).

**JobEvent** (event raiser/waiter comments): `$`, `callJobId`, `callUniqueId`, `chainJobId`, `chainOutParameters`/`.name`, `chainParameters`/`.name`, `chainQueue`, `eventDefinition` (String — name of the event definition being raised/waited for), `jobId`, `parameters`/`.name`, `parentJobId`, `queue`, `stepIterations`, `stepJobId`, `stepUniqueId`, `topLevelJobId`, `topLevelQueue`.

**JobSearch** (file search expressions): `$`, `line` (String — the string found by the file search), `partition`.

**MailJob**: `jcsJob` (Job object), `parameters`/`parameters.name`.

**MonitorAlertSource**: `alertSourceType`, `alertSourceUniqueId`, `data` (String).

**MonitorCondition**: (no documented implicit objects beyond global ones).

**OSNativeParameter**: `jobId`, `osFamily` (String — OS family of the process server), `parameters`/`parameters.name`, `parentJobId`, `queue`.

**ProcessMonitorEvaluation**: `chainParameters`/`chainParameters.name`, `monitoritem` (MapScriptObject — process monitor instance values), `parameters`/`parameters.name`.

**ProcessServerAlertSource**: `alertSourceType`, `alertSourceUniqueId`, `newStatus`, `oldStatus`, `partition`, `processServer` (String).

**ProcessServerCheckAlertSource**: `alertSourceType`, `reactionJobDefinition` (String), `reactionJobDefinitionUniqueId` (String).

**ReportColumnEvaluation**: `<Object>` (String — values of the current object's fields), `parameters`/`parameters.name`.

**ReportPreviewDefaultParameter**: `jobId`, `parameters`/`parameters.name`, `parentJobId`, `queue`.

**ReportSelectionEvaluation**: `parameters`/`parameters.name`.

**ReturnCodeMapping**: `parameters`/`parameters.name`, `returnCode` (Number).

**SAPMassActivityParameter**: `jobId`, `parameters`/`parameters.name`, `parentJobId`, `queue`.

**Simple**: `$`, `partition`.
