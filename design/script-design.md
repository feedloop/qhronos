# Qhronos Script System Design

## 1. Overview

The Script System enables JavaScript code execution within Qhronos workflows using the Goja runtime. Scripts provide powerful capabilities for data transformation, API calls, mathematical operations, and LLM interactions, all executed synchronously within workflow steps.

### Core Concepts

- **Script**: JavaScript code stored in the scripts repository
- **Execution Context**: Environment provided to scripts with input data, previous step outputs, and APIs
- **Synchronous Execution**: All operations execute synchronously within the script
- **Sandboxed Runtime**: Scripts run in an isolated Goja JavaScript runtime
- **Capabilities**: Built-in APIs for fetch, math, LLM calls, and more

---

## 2. Script Execution Model

### Execution Context

Scripts receive a `context` object containing:

```javascript
{
  input: {},           // Input data from workflow instance or step
  steps: {             // Outputs from previous steps
    step1: { output: {...} },
    step2: { output: {...} }
  },
  workflow: {          // Workflow-level variables
    variableName: value
  },
  console: {           // Console API for logging
    log: function(...args),
    error: function(...args),
    warn: function(...args),
    info: function(...args)
  }
}
```

**Direct Access:** All context properties are accessible directly without the `context.` prefix:

```javascript
// Direct access (recommended)
const userId = input.userId;
const step1Output = steps.step1.output;
const apiToken = workflow.apiToken;
console.log('Processing...');

// Context object access (also works)
const userId2 = context.input.userId;
const step1Output2 = context.steps.step1.output;
const apiToken2 = context.workflow.apiToken;
context.console.log('Processing...');
```

**Note:** Database, LLM, Spreadsheet, and File functionality are accessed via `require()`:
- `const db = require('db')('integration-id')` - Database operations via database integration
- `const llm = require('llm')('integration-id')` - LLM API calls via LLM integration
- `const sheets = require('sheets')('integration-id')` - Google Sheets operations via spreadsheet integration
- `const files = require('files')` - File operations (object storage)

### Return Value

Scripts should return a value that becomes the step output:

```javascript
// Return object (recommended)
return {
  success: true,
  data: processedData,
  message: "Processing complete"
};

// Return primitive (automatically wrapped)
return "simple string";  // Becomes { value: "simple string" }

// Throw error (step marked as failed)
throw new Error("Something went wrong");
```

---

## 3. Core JavaScript Features

### Standard JavaScript Support

The Goja runtime supports standard JavaScript features:

- **Variables and Types**: `let`, `const`, `var`, primitives, objects, arrays
- **Control Flow**: `if/else`, `switch`, `for`, `while`, `do/while`, `for...in`, `for...of`
- **Functions**: Function declarations, arrow functions, async/await (synchronous execution)
- **Objects and Arrays**: Object literals, array methods, destructuring, spread operator
- **Error Handling**: `try/catch/finally`, `throw`
- **Date and Time**: `Date` object, `Date.now()`, `new Date()`
- **JSON**: `JSON.parse()`, `JSON.stringify()`
- **String Methods**: All standard string methods
- **Array Methods**: `map`, `filter`, `reduce`, `forEach`, `find`, `some`, `every`, etc.
- **Object Methods**: `Object.keys()`, `Object.values()`, `Object.entries()`, `Object.assign()`

### Math Operations

Full `Math` object support:

```javascript
Math.abs(-5)           // 5
Math.max(1, 2, 3)      // 3
Math.min(1, 2, 3)      // 1
Math.round(3.7)        // 4
Math.floor(3.7)        // 3
Math.ceil(3.2)         // 4
Math.random()          // Random number 0-1
Math.pow(2, 3)         // 8
Math.sqrt(16)          // 4
Math.sin(Math.PI/2)    // 1
Math.cos(0)            // 1
Math.log(10)           // Natural logarithm
Math.exp(1)            // e
// ... all Math methods available
```

---

## 4. Built-in APIs

### Fetch API

Synchronous HTTP requests using the `fetch` function:

```javascript
// GET request
const response = fetch('https://api.example.com/data', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer ' + workflow.apiToken,
    'Content-Type': 'application/json'
  }
});

// POST request
const response = fetch('https://api.example.com/endpoint', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    data: input.data
  })
});

// Response handling
if (response.ok) {
  const data = response.json();
  return { success: true, data: data };
} else {
  throw new Error(`HTTP ${response.status}: ${response.statusText}`);
}
```

**Fetch API Methods:**

- `fetch(url, options)` - Make HTTP request
- `response.ok` - Boolean, true if status 200-299
- `response.status` - HTTP status code
- `response.statusText` - HTTP status text
- `response.headers` - Response headers object
- `response.json()` - Parse response as JSON
- `response.text()` - Get response as text
- `response.arrayBuffer()` - Get response as ArrayBuffer

**Request Options:**

```javascript
{
  method: 'GET|POST|PUT|DELETE|PATCH',
  headers: {
    'Header-Name': 'value'
  },
  body: 'string' | JSON.stringify(object),
  timeout: 30000  // Optional: timeout in milliseconds (default: 30s)
}
```

---

## 5. Database API

Synchronous database operations using the `db` module via database integrations. Supports both MySQL and PostgreSQL.

### Database Connection

Scripts access databases through database integrations:

```javascript
// Require db module with integration ID
const db = require('db')('mysql-integration-id');  // MySQL integration

// Use PostgreSQL integration
const pgDb = require('db')('postgres-integration-id');  // PostgreSQL integration

// Multiple database connections
const db1 = require('db')('production-db-id');
const db2 = require('db')('analytics-db-id');
```

**Note:** Database integrations must be created via the `/integrations` API endpoint before use in scripts. The integration ID is passed to `require('db')()` to access the configured database.

### Query Execution

#### Select Queries

```javascript
// Simple SELECT
const users = db.query('SELECT * FROM users WHERE status = ?', ['active']);

// With parameters
const user = db.query('SELECT * FROM users WHERE id = ?', [userId]);

// Multiple rows returned as array
const results = db.query('SELECT * FROM orders WHERE user_id = ?', [userId]);
```

#### Insert Queries

```javascript
// INSERT with parameters
const result = db.execute(
  'INSERT INTO users (name, email) VALUES (?, ?)',
  ['John Doe', 'john@example.com']
);

// Get inserted ID
const newUserId = result.insertId;  // MySQL
const newUserId = result.lastInsertId;  // PostgreSQL (alternative)
```

#### Update Queries

```javascript
// UPDATE with parameters
const result = db.execute(
  'UPDATE users SET status = ? WHERE id = ?',
  ['inactive', userId]
);

// Get affected rows
const affectedRows = result.affectedRows;
```

#### Delete Queries

```javascript
// DELETE with parameters
const result = db.execute(
  'DELETE FROM users WHERE id = ?',
  [userId]
);

// Get affected rows
const affectedRows = result.affectedRows;
```

### Transaction Support

```javascript
// Begin transaction
db.beginTransaction();

try {
  // Execute multiple queries
  db.execute('INSERT INTO orders (user_id, total) VALUES (?, ?)', [userId, total]);
  db.execute('UPDATE users SET balance = balance - ? WHERE id = ?', [total, userId]);
  
  // Commit transaction
  db.commit();
  
  return { success: true };
} catch (error) {
  // Rollback on error
  db.rollback();
  throw error;
}
```

### Query Methods

#### `db.query(sql, params)`

Execute SELECT query and return results.

**Parameters:**
- `sql` (string): SQL query with placeholders (`?` for MySQL/PostgreSQL)
- `params` (array): Parameter values

**Returns:** Array of result objects

**Example:**
```javascript
const users = db.query('SELECT * FROM users WHERE age > ?', [18]);
// Returns: [{ id: 1, name: 'John', age: 25 }, ...]
```

#### `db.queryOne(sql, params)`

Execute SELECT query and return single row.

**Parameters:**
- `sql` (string): SQL query
- `params` (array): Parameter values

**Returns:** Single result object or `null`

**Example:**
```javascript
const user = db.queryOne('SELECT * FROM users WHERE id = ?', [userId]);
// Returns: { id: 1, name: 'John', age: 25 } or null
```

#### `db.execute(sql, params)`

Execute INSERT, UPDATE, or DELETE query.

**Parameters:**
- `sql` (string): SQL query
- `params` (array): Parameter values

**Returns:** Execution result object

**Example:**
```javascript
const result = db.execute('INSERT INTO users (name) VALUES (?)', ['John']);
// Returns: { insertId: 123, affectedRows: 1 }
```

#### `db.beginTransaction()`

Begin a database transaction.

**Returns:** void

#### `db.commit()`

Commit the current transaction.

**Returns:** void

#### `db.rollback()`

Rollback the current transaction.

**Returns:** void

### Database-Specific Features

#### MySQL

```javascript
// MySQL-specific features
const result = db.execute('INSERT INTO users (name) VALUES (?)', ['John']);
const insertId = result.insertId;  // MySQL insert ID
const affectedRows = result.affectedRows;
```

#### PostgreSQL

```javascript
// PostgreSQL-specific features
const result = db.execute('INSERT INTO users (name) VALUES ($1) RETURNING id', ['John']);
const insertId = result.insertId || result.rows[0].id;  // PostgreSQL insert ID
const affectedRows = result.rowCount;
```

**Note:** For PostgreSQL, you can use `$1, $2, ...` placeholders or `?` (both supported).

### Error Handling

```javascript
try {
  const users = db.query('SELECT * FROM users WHERE id = ?', [userId]);
  return { success: true, users: users };
} catch (error) {
  console.error('Database error:', error.message);
  throw new Error(`Database query failed: ${error.message}`);
}
```

---

## 6. Module System and Require

Scripts can use `require()` to import packages and modules. The module system supports both built-in modules and custom packages.

### Require Statement

```javascript
// Require a built-in module
const crypto = require('crypto');
const uuid = require('uuid');
const validator = require('validator');

// Use the module
const hash = crypto.createHash('sha256').update('data').digest('hex');
const id = uuid.v4();
const isValidEmail = validator.isEmail('test@example.com');
```

### Built-in Modules

The following built-in modules are available:

#### `crypto` - Cryptographic Functions

```javascript
const crypto = require('crypto');

// Hash functions
const hash = crypto.createHash('sha256').update('data').digest('hex');
const md5 = crypto.createHash('md5').update('data').digest('hex');

// HMAC
const hmac = crypto.createHmac('sha256', 'secret').update('data').digest('hex');

// Random bytes
const randomBytes = crypto.randomBytes(16).toString('hex');
```

#### `uuid` - UUID Generation

```javascript
const uuid = require('uuid');

// Generate UUID v4
const id = uuid.v4();  // '550e8400-e29b-41d4-a716-446655440000'

// Generate UUID v1
const id1 = uuid.v1();

// Validate UUID
const isValid = uuid.validate(id);
```

#### `validator` - Data Validation

```javascript
const validator = require('validator');

// Email validation
const isValidEmail = validator.isEmail('test@example.com');

// URL validation
const isValidUrl = validator.isURL('https://example.com');

// String validation
const isNumeric = validator.isNumeric('123');
const isAlpha = validator.isAlpha('abc');
const isAlphanumeric = validator.isAlphanumeric('abc123');
```

#### `jsonpath` - JSON Path Queries

```javascript
const jsonpath = require('jsonpath');

const data = {
  users: [
    { id: 1, name: 'John' },
    { id: 2, name: 'Jane' }
  ]
};

// Query JSON path
const names = jsonpath.query(data, '$.users[*].name');  // ['John', 'Jane']
const firstUser = jsonpath.query(data, '$.users[0]');
```

### Custom Packages

Custom packages can be installed and made available to scripts. Packages are resolved from a configured package repository.

```javascript
// Require custom package
const myPackage = require('my-custom-package');

// Use package functions
const result = myPackage.doSomething(data);
```

### Package Resolution

1. **Built-in Modules**: Resolved from system modules
2. **Custom Packages**: Resolved from configured package repository
3. **Local Modules**: Scripts can require other scripts (future enhancement)

### Module Caching

Modules are cached after first load for performance:

```javascript
// First require - loads and caches
const crypto1 = require('crypto');

// Second require - uses cached version
const crypto2 = require('crypto');

// crypto1 === crypto2 (same instance)
```

---

## 7. LLM API

Synchronous LLM calls using the `llm` module:

```javascript
// Require llm module
const llm = require('llm');

// Simple LLM call
const result = llm({
  provider: 'openai',
  model: 'gpt-4',
  messages: [
    {
      role: 'system',
      content: 'You are a helpful assistant.'
    },
    {
      role: 'user',
      content: input.question
    }
  ],
  temperature: 0.7,
  max_tokens: 500
});

// Access response
const content = result.content;
const usage = result.usage;  // { prompt_tokens, completion_tokens, total_tokens }

return {
  success: true,
  response: content,
  tokens_used: usage.total_tokens
};
```

**LLM Function Parameters:**

```javascript
const llm = require('llm');

llm({
  provider: 'openai|anthropic|gemini|openrouter',  // Required
  model: 'gpt-4|claude-3-opus|...',                // Required
  messages: [                                       // Required
    { role: 'system|user|assistant', content: '...' }
  ],
  temperature: 0.7,                                 // Optional: 0.0-2.0
  max_tokens: 1000,                                 // Optional
  api_key: '...',                                   // Optional: uses env var if not provided
  base_url: 'https://...'                          // Optional: custom endpoint
})
```

**LLM Response:**

```javascript
{
  provider: 'openai',
  model: 'gpt-4',
  content: 'The generated text...',
  usage: {
    prompt_tokens: 10,
    completion_tokens: 20,
    total_tokens: 30
  },
  finish_reason: 'stop'
}
```

---

## 8. File API

Synchronous file operations using the `files` module. Files are stored in object storage (MinIO/S3 compatible) and support global, event-scoped, job-scoped, and workflow-scoped storage.

### File Storage Types

1. **Global Files**: Accessible across all workflows, events, and jobs
   - Path format: `global/path/to/file.txt`
   - Use for shared resources, templates, configurations

2. **Event Files**: Scoped to a specific event
   - Path format: `event/path/to/file.txt` (automatically scoped to current event)
   - Retained for recurring events (events persist for recurring events)
   - Deleted when event is deleted (one-time events after completion, recurring events when expired)
   - Use for event-specific data, configuration, state

3. **Job Files**: Scoped to a specific job execution
   - Path format: `job/path/to/file.txt` (automatically scoped to current job)
   - Deleted when job is deleted (after completion)
   - Use for job-specific temporary files, execution results

4. **Workflow Files**: Scoped to a specific workflow instance
   - Path format: `workflow/path/to/file.txt` (automatically scoped to current workflow instance)
   - Use for workflow-specific temporary files, intermediate results

### File Module

```javascript
// Require files module
const files = require('files');
```

### Reading Files

```javascript
// Read file as text
const content = files.read('global/templates/email.html');
console.log(content);

// Read file as buffer (for binary files)
const buffer = files.readBuffer('global/images/logo.png');

// Read file as JSON (automatically parsed)
const config = files.readJSON('global/config/settings.json');

// Check if file exists before reading
if (files.exists('workflow/temp/data.json')) {
  const data = files.readJSON('workflow/temp/data.json');
}
```

### Writing Files

```javascript
// Write text file
files.write('workflow/output/result.txt', 'File content here');

// Write JSON file (automatically stringified)
files.writeJSON('workflow/data/processed.json', {
  success: true,
  data: processedData
});

// Write buffer (for binary files)
const imageBuffer = fetch('https://example.com/image.png').arrayBuffer();
files.writeBuffer('workflow/images/downloaded.png', imageBuffer);

// Write with options
files.write('workflow/logs/app.log', logContent, {
  contentType: 'text/plain',
  metadata: {
    createdBy: 'script',
    workflowId: workflow.workflowId
  }
});
```

### Listing Files

```javascript
// List files in a directory (global)
const globalFiles = files.list('global/templates/');
// Returns: ['email.html', 'notification.html', 'report.html']

// List files in workflow directory
const workflowFiles = files.list('workflow/temp/');
// Returns: ['data1.json', 'data2.json']

// List with prefix filter
const jsonFiles = files.list('workflow/data/', { prefix: '*.json' });

// List recursively
const allFiles = files.list('workflow/', { recursive: true });
```

### Deleting Files

```javascript
// Delete a single file
files.delete('workflow/temp/old-data.json');

// Delete multiple files
files.delete(['workflow/temp/file1.json', 'workflow/temp/file2.json']);

// Delete directory (all files in directory)
files.deleteDir('workflow/temp/');
```

### File Information

```javascript
// Get file metadata
const info = files.info('global/templates/email.html');
// Returns: {
//   path: 'global/templates/email.html',
//   size: 1024,
//   contentType: 'text/html',
//   lastModified: '2024-01-01T00:00:00Z',
//   metadata: { ... }
// }

// Check if file exists
const exists = files.exists('workflow/output/result.txt');
```

### File Paths

**Global Files:**
- Must start with `global/`
- Accessible from any workflow, event, or job
- Example: `global/templates/email.html`, `global/config/settings.json`

**Event Files:**
- Must start with `event/`
- Automatically scoped to current event
- Path `event/data/config.json` becomes `events/{event_id}/data/config.json` in storage
- Retained for recurring events (events persist until recurrence expires)
- Deleted when event is deleted
- Example: `event/config/settings.json`, `event/data/state.json`

**Job Files:**
- Must start with `job/`
- Automatically scoped to current job
- Path `job/output/result.json` becomes `jobs/{job_id}/output/result.json` in storage
- Deleted when job is deleted (after completion)
- Example: `job/temp/processing.json`, `job/output/result.json`

**Workflow Files:**
- Must start with `workflow/`
- Automatically scoped to current workflow instance
- Path `workflow/temp/data.json` becomes `workflows/{instance_id}/temp/data.json` in storage
- Example: `workflow/output/result.json`, `workflow/temp/processing.log`

**Path Rules:**
- Paths are case-sensitive
- Use forward slashes `/` as path separators
- No leading slash required (but allowed)
- Relative paths are not supported (always use absolute paths)
- File scope is determined by prefix (`global/`, `event/`, `job/`, `workflow/`)

### Examples

**Example 1: Read Template and Process**

```javascript
const files = require('files');

// Read global template
const template = files.read('global/templates/email.html');

// Process template with data
const processed = template
  .replace('{{name}}', input.userName)
  .replace('{{message}}', input.message);

// Save processed result to workflow directory
files.write('workflow/output/email.html', processed);

return {
  success: true,
  outputFile: 'workflow/output/email.html'
};
```

**Example 2: Process and Store JSON Data**

```javascript
const files = require('files');

// Read input data
const inputData = input.data;

// Process data
const processed = inputData.map(item => ({
  ...item,
  processedAt: new Date().toISOString(),
  processedBy: workflow.workflowId
}));

// Save to workflow directory
files.writeJSON('workflow/data/processed.json', processed);

// Also save summary to global directory
files.writeJSON('global/reports/latest-summary.json', {
  count: processed.length,
  timestamp: new Date().toISOString()
});

return {
  success: true,
  processed: processed.length,
  file: 'workflow/data/processed.json'
};
```

**Example 3: File Cleanup**

```javascript
const files = require('files');

// List all temporary files
const tempFiles = files.list('workflow/temp/');

// Delete old temporary files
tempFiles.forEach(file => {
  const filePath = `workflow/temp/${file}`;
  const info = files.info(filePath);
  const age = Date.now() - new Date(info.lastModified).getTime();
  
  // Delete files older than 1 hour
  if (age > 3600000) {
    files.delete(filePath);
    console.log(`Deleted old file: ${filePath}`);
  }
});

return { success: true, cleaned: tempFiles.length };
```

**Example 4: Binary File Handling**

```javascript
const files = require('files');
const fetch = require('fetch'); // Note: fetch is global, not require

// Download image
const response = fetch('https://example.com/image.png');
const imageBuffer = response.arrayBuffer();

// Save to workflow directory
files.writeBuffer('workflow/images/downloaded.png', imageBuffer);

// Read back
const savedBuffer = files.readBuffer('workflow/images/downloaded.png');

return {
  success: true,
  fileSize: savedBuffer.length,
  file: 'workflow/images/downloaded.png'
};
```

### File API Methods

#### `files.read(path)`
Read file as text string.

**Parameters:**
- `path` (string): File path (global, event, job, or workflow)

**Returns:** String content

#### `files.readBuffer(path)`
Read file as ArrayBuffer (for binary files).

**Parameters:**
- `path` (string): File path

**Returns:** ArrayBuffer

#### `files.readJSON(path)`
Read file as JSON (automatically parsed).

**Parameters:**
- `path` (string): File path

**Returns:** Parsed JSON object

#### `files.write(path, content, options)`
Write text content to file.

**Parameters:**
- `path` (string): File path
- `content` (string): File content
- `options` (object, optional):
  - `contentType` (string): MIME type
  - `metadata` (object): Custom metadata

**Returns:** void

#### `files.writeJSON(path, data, options)`
Write JSON object to file (automatically stringified).

**Parameters:**
- `path` (string): File path
- `data` (object): JSON object to write
- `options` (object, optional): Same as `write()`

**Returns:** void

#### `files.writeBuffer(path, buffer, options)`
Write binary buffer to file.

**Parameters:**
- `path` (string): File path
- `buffer` (ArrayBuffer): Binary data
- `options` (object, optional): Same as `write()`

**Returns:** void

#### `files.list(path, options)`
List files in directory.

**Parameters:**
- `path` (string): Directory path
- `options` (object, optional):
  - `prefix` (string): Filter by prefix/pattern
  - `recursive` (boolean): List recursively

**Returns:** Array of file names

#### `files.delete(path)`
Delete file(s).

**Parameters:**
- `path` (string|array): File path or array of paths

**Returns:** void

#### `files.deleteDir(path)`
Delete all files in directory.

**Parameters:**
- `path` (string): Directory path

**Returns:** void

#### `files.exists(path)`
Check if file exists.

**Parameters:**
- `path` (string): File path

**Returns:** Boolean

#### `files.info(path)`
Get file metadata.

**Parameters:**
- `path` (string): File path

**Returns:** Object with file information

---

## 9. Utility Functions

### String Utilities

```javascript
// String manipulation helpers
str.trim()
str.toLowerCase()
str.toUpperCase()
str.substring(start, end)
str.replace(pattern, replacement)
str.split(delimiter)
str.includes(substring)
str.startsWith(prefix)
str.endsWith(suffix)
```

### Array Utilities

```javascript
// Array operations
arr.map(fn)
arr.filter(fn)
arr.reduce(fn, initial)
arr.forEach(fn)
arr.find(fn)
arr.findIndex(fn)
arr.some(fn)
arr.every(fn)
arr.includes(item)
arr.indexOf(item)
arr.slice(start, end)
arr.concat(otherArray)
arr.sort(fn)
arr.reverse()
```

### Object Utilities

```javascript
// Object operations
Object.keys(obj)
Object.values(obj)
Object.entries(obj)
Object.assign(target, ...sources)
Object.hasOwnProperty(key)
```

---

## 9. Error Handling

### Try-Catch Blocks

```javascript
try {
  const response = fetch('https://api.example.com/data');
  const data = response.json();
  return { success: true, data: data };
} catch (error) {
  console.error('Fetch failed:', error.message);
  throw new Error(`Failed to fetch data: ${error.message}`);
}
```

### Error Types

```javascript
// Standard Error
throw new Error('Something went wrong');

// Custom error with details
throw {
  message: 'Custom error',
  code: 'CUSTOM_ERROR',
  details: { ... }
};
```

---

## 9. Examples

### Example 1: Data Transformation

```javascript
// Transform input data
const items = input.items || [];

const transformed = items.map(item => ({
  id: item.id,
  name: item.name.toUpperCase(),
  price: Math.round(item.price * 1.1), // Add 10% tax
  timestamp: Date.now()
}));

return {
  success: true,
  count: transformed.length,
  items: transformed
};
```

### Example 2: API Call and Processing

```javascript
// Fetch data from API
const response = fetch('https://api.example.com/users', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer ' + workflow.apiToken
  }
});

if (!response.ok) {
  throw new Error(`API call failed: ${response.status}`);
}

const users = response.json();

// Process users
const activeUsers = users.filter(user => user.status === 'active');
const totalAge = activeUsers.reduce((sum, user) => sum + user.age, 0);
const avgAge = totalAge / activeUsers.length;

return {
  success: true,
  total_users: users.length,
  active_users: activeUsers.length,
  average_age: Math.round(avgAge)
};
```

### Example 3: LLM Processing

```javascript
// Require llm module
const llm = require('llm');

// Call LLM to analyze data
const analysis = llm({
  provider: 'openai',
  model: 'gpt-4',
  messages: [
    {
      role: 'system',
      content: 'You are a data analyst. Analyze the provided data and provide insights.'
    },
    {
      role: 'user',
      content: `Analyze this data: ${JSON.stringify(input.data)}`
    }
  ],
  temperature: 0.7,
  max_tokens: 500
});

return {
  success: true,
  analysis: analysis.content,
  tokens_used: analysis.usage.total_tokens
};
```

### Example 4: Complex Workflow

```javascript
// Fetch data, process with LLM, and transform
// Step 1: Fetch external data
const apiResponse = fetch('https://api.example.com/data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: input.query })
});

const apiData = apiResponse.json();

// Step 2: Use LLM to summarize
const summary = llm({
  provider: 'openai',
  model: 'gpt-4',
  messages: [
    {
      role: 'user',
      content: `Summarize: ${JSON.stringify(apiData)}`
    }
  ]
});

// Step 3: Calculate statistics
const values = apiData.values || [];
const stats = {
  count: values.length,
  sum: values.reduce((a, b) => a + b, 0),
  avg: values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0,
  min: values.length > 0 ? Math.min(...values) : 0,
  max: values.length > 0 ? Math.max(...values) : 0
};

return {
  success: true,
  summary: summary.content,
  statistics: stats,
  tokens_used: summary.usage.total_tokens
};
```

---

## 10. Limitations and Constraints

### Synchronous Execution

- All operations execute synchronously
- No true async/await (operations block until complete)
- Script execution respects step timeout
- Long-running operations may timeout

### Sandbox Restrictions

- **File System Access**: Only via `require('files')` module (object storage: MinIO/S3 compatible, no local file system)
- **No Network Access**: Only via `fetch` API (controlled)
- **No Process Execution**: Cannot spawn processes
- **Module System**: Limited to approved packages via `require()`
- **Limited Global Objects**: Only approved globals available
- **Database Access**: Only via `require('db')` module with configured connections
- **LLM Access**: Only via `require('llm')` module
- **Spreadsheet Access**: Only via `require('sheets')` module with configured integrations
- **File Access**: Only via `require('files')` module (object storage: MinIO/S3 compatible)
- **Read-Only by Default**: Database connections may be read-only depending on configuration
- **Package Restrictions**: Only pre-approved packages available (no npm install)

### Resource Limits

- **Memory**: Limited memory allocation per script execution
- **Timeout**: Script execution respects step timeout (default: 10s, configurable)
- **API Rate Limits**: Fetch and LLM calls subject to provider rate limits
- **Max Execution Time**: Enforced by step timeout configuration

---

## 12. Best Practices

### Error Handling

```javascript
// Always handle errors
try {
  const result = fetch('https://api.example.com/data');
  return { success: true, data: result.json() };
} catch (error) {
  console.error('Error:', error.message);
  return { success: false, error: error.message };
}
```

### Input Validation

```javascript
// Validate input data
if (!input || !input.data) {
  throw new Error('Missing required input: data');
}

if (!Array.isArray(input.data)) {
  throw new Error('Input data must be an array');
}
```

### Logging

```javascript
// Use console for debugging
console.log('Processing started');
console.info('Input data:', input);
console.warn('Warning: Large dataset');
console.error('Error occurred:', error);
```

### Performance

```javascript
// Use efficient algorithms
// Good: Use map/filter/reduce
const processed = data.map(item => transform(item));

// Avoid: Nested loops when possible
// Prefer: Single pass operations
```

---

## 13. Security Considerations

### Input Sanitization

- Scripts receive input data as-is
- Validate and sanitize input before processing
- Be cautious with user-provided data

### API Key Management

- Use workflow variables for API keys
- Never hardcode secrets in scripts
- Use environment variables via `workflow` (direct access) or `context.workflow`

### Database Security

- **SQL Injection Prevention**: Always use parameterized queries
- **Connection Limits**: Database connections are pooled and limited
- **Read-Only Access**: Use read-only connections when possible
- **Transaction Timeout**: Transactions have timeout limits
- **Query Timeout**: Long-running queries may timeout
- **Access Control**: Database access controlled by workflow configuration

### Output Validation

- Validate script output before returning
- Ensure output matches expected format
- Handle edge cases gracefully

---

## 14. Integration with Workflows

### Accessing Previous Steps

```javascript
// Access previous step outputs
const step1Output = steps.step1.output;
const step2Data = steps.step2.output.data;

// Use in processing
const combined = {
  ...step1Output,
  ...step2Data
};
```

### Using Workflow Variables

```javascript
// Access workflow variables
const apiKey = workflow.apiKey;
const config = workflow.config;
const retryCount = workflow.retryCount || 0;

// Use in API calls
const response = fetch('https://api.example.com/data', {
  headers: {
    'Authorization': 'Bearer ' + apiKey
  }
});

// Update variables based on processing
const newRetryCount = retryCount + 1;
```

### Setting Workflow Variables

Scripts can set workflow variables by returning an object with a `_variables` key:

```javascript
// Set variables and return output
return {
  _variables: {
    processedCount: 10,
    lastProcessedId: "abc123",
    status: "completed",
    retryCount: workflow.retryCount + 1
  },
  success: true,
  processed: true,
  data: transformedData
};

// Variables are merged with existing workflow variables
// New values override existing ones
// Variables persist for subsequent steps
```

**Variable Assignment Rules:**
- Variables set via `_variables` are merged with existing workflow variables
- New variable values override existing ones
- Variables persist throughout the workflow instance execution
- Variables are accessible in:
  - Template strings: `{{workflow.variableName}}`
  - Condition expressions: `workflow.variableName`
  - Subsequent scripts: `workflow.variableName` (direct access) or `context.workflow.variableName`

**Example:**
```javascript
// Process data and track progress
const currentCount = workflow.processedCount || 0;

// Process items
const items = input.items || [];
const processed = items.map(item => processItem(item));

// Set variables and return result
return {
  _variables: {
    processedCount: currentCount + processed.length,
    lastProcessedAt: new Date().toISOString(),
    status: processed.length > 0 ? "processing" : "complete"
  },
  success: true,
  processed: processed.length,
  data: processed
};
```

### Returning Step Output

```javascript
// Return value becomes step output
return {
  success: true,
  processed: true,
  data: transformedData
};

// Next step can access via steps.scriptStep.output (direct access) or context.steps.scriptStep.output

// Or return with variables
return {
  _variables: {
    myVar: "value"
  },
  success: true,
  data: transformedData
};
```

---

## 13. API Reference

### Global Functions

#### `fetch(url, options)`

Make synchronous HTTP request.

**Parameters:**
- `url` (string): Request URL
- `options` (object): Request options
  - `method` (string): HTTP method
  - `headers` (object): Request headers
  - `body` (string): Request body
  - `timeout` (number): Timeout in milliseconds

**Returns:** Response object

### Module System

#### `require(moduleName)`

Load a module or package.

**Parameters:**
- `moduleName` (string): Name of the module or package

**Returns:** Module exports object

**Available Modules:**
- `db` - Database operations (MySQL/PostgreSQL)
- `llm` - LLM API calls (OpenAI, Anthropic, Gemini, OpenRouter)
- `files` - File operations (object storage: MinIO/S3 compatible)
- `crypto` - Cryptographic functions
- `uuid` - UUID generation
- `validator` - Data validation
- `jsonpath` - JSON path queries

**Example:**
```javascript
const db = require('db');
const llm = require('llm');
const files = require('files');
const uuid = require('uuid');
const crypto = require('crypto');
const validator = require('validator');
```

#### Database Module: `require('db')`

Database connection module for MySQL and PostgreSQL.

**Usage:**
```javascript
const db = require('db');  // Default connection
const db2 = require('db')('custom_connection');  // Named connection
```

**Methods:**
- `db.query(sql, params)` - Execute SELECT query, returns array
- `db.queryOne(sql, params)` - Execute SELECT query, returns single row or null
- `db.execute(sql, params)` - Execute INSERT/UPDATE/DELETE, returns result object
- `db.beginTransaction()` - Begin transaction
- `db.commit()` - Commit transaction
- `db.rollback()` - Rollback transaction

**Example:**
```javascript
const db = require('db');
const users = db.query('SELECT * FROM users WHERE status = ?', ['active']);
```

#### LLM Module: `require('llm')`

LLM API module for calling Large Language Models.

**Usage:**
```javascript
const llm = require('llm');
```

**Function:**
- `llm(params)` - Make synchronous LLM API call

**Parameters:**
- `provider` (string): Provider name (openai, anthropic, gemini, openrouter)
- `model` (string): Model identifier
- `messages` (array): Message array
- `temperature` (number): Optional, 0.0-2.0
- `max_tokens` (number): Optional
- `api_key` (string): Optional

**Returns:** LLM response object

**Example:**
```javascript
const llm = require('llm');
const result = llm({
  provider: 'openai',
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Hello' }]
});
```

#### Sheets Module: `require('sheets')`

Google Sheets API module for reading, writing, and manipulating spreadsheet data.

**Usage:**
```javascript
const sheets = require('sheets')('integration-id');  // Google Sheets integration
```

**Note:** Google Sheets integrations must be created via the `/integrations` API endpoint before use in scripts. The integration ID is passed to `require('sheets')()` to access the configured Google Sheets connection.

**Methods:**
- `sheets.getSpreadsheet(spreadsheetId)` - Get spreadsheet metadata
- `sheets.getValues(spreadsheetId, range)` - Read values from a range
- `sheets.setValues(spreadsheetId, range, values)` - Write values to a range
- `sheets.appendValues(spreadsheetId, range, values)` - Append values to a range
- `sheets.clearValues(spreadsheetId, range)` - Clear values in a range
- `sheets.batchGetValues(spreadsheetId, ranges)` - Read multiple ranges
- `sheets.batchSetValues(spreadsheetId, data)` - Write to multiple ranges
- `sheets.addSheet(spreadsheetId, title)` - Add a new sheet
- `sheets.deleteSheet(spreadsheetId, sheetId)` - Delete a sheet
- `sheets.copySheet(spreadsheetId, sheetId, destinationSpreadsheetId)` - Copy a sheet

**Examples:**

```javascript
const sheets = require('sheets')('my-sheets-integration');

// Read values from a range
const data = sheets.getValues('spreadsheet-id', 'Sheet1!A1:D10');
console.log(data);  // [['Name', 'Email', 'Age', 'Status'], ['John', 'john@example.com', 25, 'Active'], ...]

// Write values to a range
sheets.setValues('spreadsheet-id', 'Sheet1!A1:C2', [
  ['Name', 'Email', 'Score'],
  ['Alice', 'alice@example.com', 95]
]);

// Append values (adds new rows after existing data)
sheets.appendValues('spreadsheet-id', 'Sheet1!A:C', [
  ['Bob', 'bob@example.com', 88],
  ['Carol', 'carol@example.com', 92]
]);

// Clear a range
sheets.clearValues('spreadsheet-id', 'Sheet1!A1:D10');

// Read multiple ranges at once
const multiData = sheets.batchGetValues('spreadsheet-id', [
  'Sheet1!A1:B5',
  'Sheet2!C1:D5'
]);

// Write to multiple ranges at once
sheets.batchSetValues('spreadsheet-id', [
  { range: 'Sheet1!A1:B2', values: [['A1', 'B1'], ['A2', 'B2']] },
  { range: 'Sheet2!A1:B2', values: [['X1', 'Y1'], ['X2', 'Y2']] }
]);

// Get spreadsheet metadata
const meta = sheets.getSpreadsheet('spreadsheet-id');
console.log(meta.title);
console.log(meta.sheets.map(s => s.title));

// Add a new sheet
const newSheet = sheets.addSheet('spreadsheet-id', 'NewSheetName');

// Use default spreadsheet ID from integration config
const sheetsDefault = require('sheets')('integration-with-default-spreadsheet');
const data2 = sheetsDefault.getValues(null, 'Sheet1!A1:D10');  // Uses default spreadsheet ID
```

**Common Use Cases:**

```javascript
// Export data to Google Sheets
const db = require('db')('my-db');
const sheets = require('sheets')('my-sheets');

const users = db.query('SELECT name, email, created_at FROM users WHERE active = ?', [true]);
const rows = users.map(u => [u.name, u.email, u.created_at]);

// Add header and write
sheets.setValues('report-spreadsheet-id', 'Sheet1!A1', [
  ['Name', 'Email', 'Created At'],
  ...rows
]);

// Import data from Google Sheets to database
const importData = sheets.getValues('import-spreadsheet-id', 'Data!A2:C100');  // Skip header row
for (const row of importData) {
  const [name, email, status] = row;
  if (name && email) {
    db.execute('INSERT INTO leads (name, email, status) VALUES (?, ?, ?) ON CONFLICT (email) DO UPDATE SET status = ?', 
      [name, email, status, status]);
  }
}

// Aggregate data and update summary sheet
const summary = db.query(`
  SELECT DATE(created_at) as date, COUNT(*) as count, SUM(amount) as total
  FROM orders WHERE created_at >= NOW() - INTERVAL '7 days'
  GROUP BY DATE(created_at) ORDER BY date
`);
const summaryRows = summary.map(s => [s.date, s.count, s.total]);
sheets.setValues('analytics-spreadsheet-id', 'Weekly!A2:C', summaryRows);
```

#### Files Module: `require('files')`

File operations module for object storage (MinIO/S3 compatible).

**Usage:**
```javascript
const files = require('files');
```

**Methods:**
- `files.read(path)` - Read file as text
- `files.readBuffer(path)` - Read file as binary buffer
- `files.readJSON(path)` - Read and parse JSON file
- `files.write(path, content, options)` - Write text file
- `files.writeJSON(path, data, options)` - Write JSON file
- `files.writeBuffer(path, buffer, options)` - Write binary file
- `files.list(path, options)` - List files in directory
- `files.delete(path)` - Delete file(s)
- `files.deleteDir(path)` - Delete directory
- `files.exists(path)` - Check if file exists
- `files.info(path)` - Get file metadata

**File Paths:**
- Global files: `global/path/to/file.txt` (accessible across all workflows, events, jobs)
- Event files: `event/path/to/file.txt` (scoped to current event, retained for recurring events)
- Job files: `job/path/to/file.txt` (scoped to current job, deleted when job completes)
- Workflow files: `workflow/path/to/file.txt` (scoped to current workflow instance)

**Example:**
```javascript
const files = require('files');

// Read global template
const template = files.read('global/templates/email.html');

// Write event file (retained for recurring events)
files.writeJSON('event/config/settings.json', { lastRun: new Date().toISOString() });

// Write job file (deleted when job completes)
files.writeJSON('job/output/result.json', { success: true });

// Write workflow file
files.writeJSON('workflow/output/result.json', { success: true });

// List files
const jobFiles = files.list('job/output/');
const eventFiles = files.list('event/data/');
const workflowFiles = files.list('workflow/output/');
```

### Global Objects

#### `console`

Console API for logging:
- `console.log(...args)`
- `console.error(...args)`
- `console.warn(...args)`
- `console.info(...args)`

#### `Math`

Standard Math object with all methods:
- `Math.abs()`, `Math.max()`, `Math.min()`
- `Math.round()`, `Math.floor()`, `Math.ceil()`
- `Math.random()`, `Math.pow()`, `Math.sqrt()`
- `Math.sin()`, `Math.cos()`, `Math.log()`, etc.

#### `JSON`

JSON parsing and stringification:
- `JSON.parse(string)`
- `JSON.stringify(object)`

#### `Date`

Date and time operations:
- `new Date()`
- `Date.now()`
- Date methods: `getTime()`, `getFullYear()`, etc.

---

## 16. Future Enhancements

### Planned Features

1. **Extended Package Support**: More npm packages available via require
2. **Local Script Modules**: Require other scripts as modules
3. **Package Versioning**: Specify package versions in require
4. **Caching**: Cache API responses and LLM results
5. **Batch Operations**: Batch API calls for efficiency
6. **Streaming**: Support for streaming LLM responses
7. **Custom Functions**: User-defined utility functions
8. **TypeScript Support**: Type checking and IntelliSense
9. **Testing Framework**: Unit testing for scripts
10. **Performance Monitoring**: Execution time and resource usage tracking
11. **Database Query Builder**: Fluent query builder API
12. **Database Migrations**: Script-based database migrations
13. **Connection Pooling**: Advanced connection pool management
14. **Query Caching**: Cache frequently used database queries

---

## Summary

The Script System provides a powerful, synchronous JavaScript execution environment within Qhronos workflows. With support for fetch, math operations, LLM calls (via `require('llm')`), database operations (via `require('db')`), Google Sheets operations (via `require('sheets')`), module system with require, and standard JavaScript features, scripts enable complex data processing, API integration, database interactions, spreadsheet automation, and AI-powered transformations while maintaining security through sandboxed execution.

**Key Capabilities:**
- **HTTP Requests**: Synchronous fetch API for external API calls
- **Database Operations**: Full CRUD support for MySQL and PostgreSQL via `require('db')`
- **LLM Integration**: Direct LLM API calls via `require('llm')` for AI-powered processing
- **Spreadsheet Operations**: Google Sheets read/write via `require('sheets')` for data import/export
- **Math Operations**: Complete Math object support for calculations
- **Module System**: Require statement for packages (db, llm, sheets, crypto, uuid, validator, jsonpath)
- **Data Transformation**: Standard JavaScript and utility packages for data manipulation
- **Transaction Support**: Database transactions for data consistency
- **Error Handling**: Comprehensive error handling and logging
- **Package Ecosystem**: Built-in modules for common operations (validation, date handling, utilities)

