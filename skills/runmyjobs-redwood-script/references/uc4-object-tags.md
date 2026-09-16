# UC4 ↔ RunMyJobs Mapping via `UC4ExternalBusinessKey`

Read this for anything involving migration lineage between Automic UC4/AE and RunMyJobs.

During and after migration, objects keep their mapping through Redwood `ObjectTag`s. The
examples below use the default bare-script shape (see `references/runtime-and-shapes.md`): a
single local class, `Uc4Ops`, whose instance methods call each other directly.

## Tag definition and value format

- **Definition name**: `UC4ExternalBusinessKey`, residing in `Partition.GLOBAL`.
- **Value structure**: four comma-separated fields.

```
"<PackageId>, <UC4System>, <UC4Client>, <UC4ObjectName>"
```

| Index | Field           | Meaning                       | Example            |
| :---- | :-------------- | :---------------------------- | :----------------- |
| `0`   | Package ID      | Migration package / wave ID   | `MIG_WAVE_2`       |
| `1`   | UC4 System      | UC4 server / environment name | `PROD_AE`          |
| `2`   | UC4 Client      | UC4 client number             | `0100`             |
| `3`   | UC4 Object Name | Original UC4 job / chain name | `JOBS_SAP_FI_POST` |

Always `.trim()` each split part — the canonical format uses `", "` separators, but spacing is
not guaranteed to be consistent across migration waves.

## RMJ → UC4 lookup

Inspect the tags on a `JobDefinition`:

```java
for (ObjectTag tag : jd.getObjectTags()) {
  if ("UC4ExternalBusinessKey".equals(tag.getObjectTagDefinition().getName())) {
    String[] parts = tag.getValue().split(",");
    String uc4System = parts.length > 1 ? parts[1].trim() : "";
    String uc4Name   = parts.length > 3 ? parts[3].trim() : "";
  }
}
```

## UC4 → RMJ reverse lookup

Query `ObjectTag` directly, constraining the referenced object type through an
`ObjectDefinition` subquery and restricting to master definitions:

```sql
select ot.RefUniqueId, ot.Value, ot.Partition
from ObjectTag ot
where ot.ObjectTagDefinition = ?
  and ot.ObjectDefinition = (select od.UniqueId from ObjectDefinition od where od.ObjectName = 'JobDefinition')
  and ot.Value like ?
  and ot.RefUniqueId in (select jd.UniqueId from JobDefinition jd where jd.UniqueId = jd.MasterJobDefinition)
```

Bind parameter 1 = `uc4TagDef.getUniqueId()`, parameter 2 = `"%, " + uc4Name` (or
`"%," + uc4Name`). The `like` pattern is deliberately loose — **re-verify in the callback**
with `tagValue.endsWith(", " + uc4Name)`, otherwise a UC4 name that is a suffix of another
name will produce false matches.

Resolve `RefUniqueId` back to objects with
`jcsSession.getSchedulerEntityByObjectTypeUniqueId("JobDefinition", id)`.

## Split objects and siblings

A single UC4 job may have been divided into several RMJ `JobDefinition`s. All resulting
siblings carry the **same** UC4 object name in their `UC4ExternalBusinessKey` tag.

To find siblings: look up by the UC4 name, then exclude the source definition's own
`getUniqueId()`. A one-to-one mapping cannot be assumed anywhere in migration tooling — always
handle the multi-result case.

## Master vs branched / versioned definitions

Filter for master definitions to avoid targeting temporary or branched LLP instances:

- `jd.getUniqueId().equals(jd.getMasterJobDefinition().getUniqueId())`, or
- `jd.getBranchedLLPVersion() < 0`

Skipping this filter is the usual cause of a UC4 lookup returning unexpected draft or
versioned objects.

## Complete pattern: parse, reverse-lookup, siblings, and write

One local class covering the read side (`getMetadata`), the reverse lookup
(`findByUc4Name`), sibling resolution (`findSiblings`, which calls the other two), and the
write side (`setTag`). Grouping them in one class lets `findSiblings` call `getMetadata` and
`findByUc4Name` directly as ordinary method calls.

```java
import com.redwood.scheduler.api.model.*;
import com.redwood.scheduler.api.model.interfaces.*;
import java.util.*;
import java.sql.*;
{
  class Uc4Metadata {
    String packageId, uc4System, uc4Client, uc4Name, rawTagValue;
  }

  class Uc4Ops {
    Uc4Metadata getMetadata(JobDefinition jd) {
      for (ObjectTag tag : jd.getObjectTags()) {
        if ("UC4ExternalBusinessKey".equals(tag.getObjectTagDefinition().getName())) {
          String raw = tag.getValue();
          if (raw == null || raw.trim().isEmpty()) return null;

          String[] parts = raw.split(",");
          Uc4Metadata meta = new Uc4Metadata();
          meta.rawTagValue = raw;
          meta.packageId = parts.length > 0 ? parts[0].trim() : "";
          meta.uc4System = parts.length > 1 ? parts[1].trim() : "";
          meta.uc4Client = parts.length > 2 ? parts[2].trim() : "";
          meta.uc4Name   = parts.length > 3 ? parts[3].trim() : "";
          return meta;
        }
      }
      return null; // no UC4 tag on this definition
    }

    List<JobDefinition> findByUc4Name(String uc4Name, Partition optionalPartition) throws Exception {
      Partition global = jcsSession.getPartitionByName("GLOBAL");
      ObjectTagDefinition uc4TagDef = jcsSession.getObjectTagDefinitionByName(global, "UC4ExternalBusinessKey");
      if (uc4TagDef == null) {
        throw new IllegalStateException("ObjectTagDefinition 'UC4ExternalBusinessKey' not found in GLOBAL partition");
      }

      String likePattern = "%, " + uc4Name.trim();
      String sql = "select ot.RefUniqueId, ot.Value, ot.Partition "
                 + "from ObjectTag ot "
                 + "where ot.ObjectTagDefinition = ? "
                 + "  and ot.ObjectDefinition = (select od.UniqueId from ObjectDefinition od where od.ObjectName = 'JobDefinition') "
                 + "  and ot.Value like ? "
                 + "  and ot.RefUniqueId in (select jd.UniqueId from JobDefinition jd where jd.UniqueId = jd.MasterJobDefinition) "
                 + (optionalPartition != null ? "  and ot.Partition = ? " : "");

      Object[] params = optionalPartition != null
          ? new Object[] { uc4TagDef.getUniqueId(), likePattern, optionalPartition.getUniqueId() }
          : new Object[] { uc4TagDef.getUniqueId(), likePattern };

      List<Long> matchedIds = new ArrayList<>();
      jcsSession.executeQuery(sql, params, new APIResultSetCallback() {
        public boolean callback(ResultSet rs, ObjectGetter og) throws SQLException {
          String tagValue = rs.getString(2);
          if (tagValue != null && tagValue.endsWith(", " + uc4Name.trim())) {
            matchedIds.add(rs.getLong(1));
          }
          return true;
        }
        public void start() {}
        public void finish() {}
      });

      List<JobDefinition> result = new ArrayList<>();
      for (Long id : matchedIds) {
        SchedulerEntity se = jcsSession.getSchedulerEntityByObjectTypeUniqueId("JobDefinition", id);
        if (se instanceof JobDefinition) {
          result.add((JobDefinition) se);
        }
      }
      return result;
    }

    List<JobDefinition> findSiblings(JobDefinition sourceJd) throws Exception {
      Uc4Metadata meta = getMetadata(sourceJd);
      if (meta == null || meta.uc4Name.isEmpty()) {
        return Collections.emptyList();
      }

      List<JobDefinition> siblings = new ArrayList<>();
      for (JobDefinition match : findByUc4Name(meta.uc4Name, null)) {
        if (!match.getUniqueId().equals(sourceJd.getUniqueId())) {
          siblings.add(match);
        }
      }
      return siblings;
    }

    void setTag(JobDefinition jd, String packageId, String uc4System, String uc4Client, String uc4Name) throws Exception {
      Partition global = jcsSession.getPartitionByName("GLOBAL");
      ObjectTagDefinition uc4TagDef = jcsSession.getObjectTagDefinitionByName(global, "UC4ExternalBusinessKey");
      if (uc4TagDef == null) {
        uc4TagDef = jcsSession.createObjectTagDefinition();
        uc4TagDef.setName("UC4ExternalBusinessKey");
        uc4TagDef.setPartition(global);
      }

      ObjectTag ot = jd.getObjectTagByObjectTagDefinition(uc4TagDef);
      if (ot == null) {
        ot = jd.createObjectTag(uc4TagDef);
      }

      // Every component trimmed individually - a trailing space anywhere makes persist() throw
      String safePackage = packageId != null ? packageId.trim() : "";
      String safeSystem  = uc4System != null ? uc4System.trim() : "";
      String safeClient  = uc4Client != null ? uc4Client.trim() : "";
      String safeName    = uc4Name   != null ? uc4Name.trim()   : "";

      ot.setValue(safePackage + ", " + safeSystem + ", " + safeClient + ", " + safeName);
      jcsSession.persist();
      jcsOut.println("Set UC4ExternalBusinessKey on " + jd.getName() + " -> " + ot.getValue());
    }
  }

  Uc4Ops ops = new Uc4Ops();
  Partition partition = jcsSession.getPartitionByName("P1112");
  JobDefinition jd = jcsSession.getJobDefinitionByName(partition, "JSAP_XOE_011_ERS");

  Uc4Metadata meta = ops.getMetadata(jd);
  if (meta != null) {
    jcsOut.println("UC4 name: " + meta.uc4Name);
    for (JobDefinition sibling : ops.findSiblings(jd)) {
      jcsOut.println("  sibling: " + sibling.getName());
    }
  }
}
```

Every component of the tag value must be trimmed before concatenation — a trailing space
anywhere makes `persist()` throw.
