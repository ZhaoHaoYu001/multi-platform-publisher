# Python异步编程入门：从零开始掌握async/await

> 异步编程是现代Python开发的必备技能，让我们一起探索这个强大的特性！

## 为什么需要异步编程？

在传统的同步编程中，当程序遇到I/O操作（如网络请求、文件读写）时，会**阻塞等待**直到操作完成。这意味着：

- CPU处于空闲状态
- 程序无法处理其他任务
- 整体性能受到影响

异步编程允许程序在等待I/O时**继续执行其他任务**，大大提高了效率。

## 核心概念

### 1. 协程（Coroutine）

协程是异步编程的基础，使用 `async def` 定义：

```python
import asyncio

async def hello():
    print("Hello")
    await asyncio.sleep(1)
    print("World")
```

### 2. await关键字

`await` 用于等待一个协程完成：

```python
async def fetch_data():
    print("开始获取数据...")
    await asyncio.sleep(2)  # 模拟网络请求
    print("数据获取完成!")
    return {"status": "success", "data": [1, 2, 3]}
```

### 3. 事件循环（Event Loop）

事件循环是异步编程的核心，负责调度和执行协程：

```python
async def main():
    # 同时运行多个协程
    results = await asyncio.gather(
        fetch_data(),
        fetch_data(),
        fetch_data()
    )
    print(f"获取到 {len(results)} 个结果")

# 运行事件循环
asyncio.run(main())
```

## 实战示例

### 异步HTTP请求

使用 `aiohttp` 进行并发请求：

```python
import aiohttp
import asyncio

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# 使用示例
urls = [
    "https://api.github.com",
    "https://httpbin.org/get",
    "https://jsonplaceholder.typicode.com/posts/1"
]
```

### 异步文件操作

使用 `aiofiles` 进行异步文件读写：

```python
import aiofiles
import asyncio

async def read_file(filename):
    async with aiofiles.open(filename, 'r') as f:
        content = await f.read()
        return content

async def write_file(filename, content):
    async with aiofiles.open(filename, 'w') as f:
        await f.write(content)
```

## 最佳实践

1. **避免在异步函数中使用阻塞操作**
   - 使用 `asyncio.to_thread()` 包装阻塞函数
   - 使用异步版本的库（aiohttp, aiofiles等）

2. **合理使用 `asyncio.gather()` 和 `asyncio.create_task()`**
   - `gather()` 用于等待多个协程
   - `create_task()` 用于调度后台任务

3. **注意异常处理**
   - 使用 `try/except` 捕获异常
   - 使用 `asyncio.Task` 的 `add_done_callback()` 处理结果

## 性能对比

让我们看一个简单的性能测试：

| 方式 | 10个请求耗时 | 100个请求耗时 |
|------|-------------|--------------|
| 同步 | ~10秒 | ~100秒 |
| 异步 | ~1秒 | ~2秒 |

> 💡 **提示**：异步编程特别适合I/O密集型任务，如网络请求、数据库操作等。

## 总结

异步编程是Python中处理并发的重要工具：

- 使用 `async/await` 定义和调用协程
- 使用 `asyncio.run()` 运行主协程
- 使用 `asyncio.gather()` 并发执行多个任务
- 选择异步版本的第三方库

---

**下一步学习**：
- [Python官方文档：asyncio](https://docs.python.org/3/library/asyncio.html)
- [aiohttp文档](https://docs.aiohttp.org/)
- [Real Python：Async IO in Python](https://realpython.com/async-io-python/)

*发布日期：2024年5月*
