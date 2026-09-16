# Query Execution Modes

RunMyJobs queries can be executed in three primary environments:
1. The Redwood Web UI (Support Query / SQL Console)
2. In Java / RedwoodScript via `executeObjectQuery` (Entity objects)
3. In Java / RedwoodScript via `executeQuery` (Tabular result set projection)

---

## 1. Redwood Web UI / Support Query Console

In the Redwood Support Query Console or custom Redwood SQL query page, paste pure ANSI SQL'92 queries:

```sql
SELECT jd.Name AS JobDefinitionName,
       jd1.Name AS ParentName
FROM JobDefinition jd
JOIN JobChainCall jcc ON jcc.JobDefinition = jd.UniqueId
JOIN JobChainStep jcs ON jcc.JobChainStep = jcs.UniqueId
JOIN JobChain jc ON jcs.JobChain = jc.UniqueId
JOIN JobDefinition jd1 ON jc.JobDefinition = jd1.UniqueId
WHERE jd.Name IN ('MY_JOB_NAME')
  AND jd.BranchedLLPVersion = -1
  AND jd1.BranchedLLPVersion = -1
```

- Results are rendered directly in a table/grid.
- Ideal for quick audits, ad-hoc searches, and verifying data relationships.

---

## 2. In RedwoodScript: `executeObjectQuery` (Objects)

When your script needs to iterate over hydrated Redwood Java objects (`JobDefinition`, `Job`, etc.):

### Untyped Iterator
```java
String sql = "select jd.* from JobDefinition jd where jd.Name like 'SAP_%' and jd.BranchedLLPVersion = -1";
for (Iterator it = jcsSession.executeObjectQuery(sql, null); it.hasNext();) {
    JobDefinition jd = (JobDefinition) it.next();
    jcsOut.println("Found job: " + jd.getName() + " in partition " + jd.getPartition().getName());
}
```

### Typed `RWIterable`
```java
String sql = "select jd.* from JobDefinition jd where jd.ParentApplication = ? and jd.BranchedLLPVersion = -1";
Application app = jcsSession.getApplicationByName("FINANCE");
for (JobDefinition jd : jcsSession.executeObjectQuery(JobDefinition.TYPE, sql, new Object[] { app.getUniqueId() })) {
    jcsOut.println("Finance Job: " + jd.getName());
}
```

---

## 3. In RedwoodScript: `executeQuery` (Tabular Projection)

When you need column projections, scalar values, aggregations (`COUNT(*)`, `SUM`, `DISTINCT`), or multi-table joins where you only want specific columns rather than entire hydrated entities:

```java
import com.redwood.scheduler.api.model.*;
import java.sql.ResultSet;
import java.sql.SQLException;

String sql = "SELECT jd.Name AS JobName, jp.Name AS ParamName, jp.DefaultExpression AS Val "
           + "FROM JobDefinition jd "
           + "JOIN JobDefinitionParameter jp ON jp.JobDefinition = jd.UniqueId "
           + "WHERE jd.Name = ? AND jd.BranchedLLPVersion = -1";

Object[] params = new Object[] { "MY_JOB_DEF" };

jcsSession.executeQuery(sql, params, new APIResultSetCallback() {
    public void start() {
        jcsOut.println("Starting parameter dump...");
    }

    public boolean callback(ResultSet rs, ObjectGetter og) throws SQLException {
        // ResultSet column index is 1-based matching SELECT clause
        String jobName = rs.getString(1);
        String paramName = rs.getString(2);
        String val = rs.getString(3);
        jcsOut.println(jobName + "." + paramName + " = " + val);
        return true; // return false to stop iteration early
    }

    public void finish() {
        jcsOut.println("Parameter dump complete.");
    }
});
```
