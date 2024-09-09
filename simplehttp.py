import html
import http.server
import inspect
import requests
import time
import tracemalloc

TEST_API_URL = "https://demo.nautobot.com"
TEST_API_TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
TEST_API_HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Token {TEST_API_TOKEN}",
}


HTML_BODY = """
<html>
    <head>
        <title>Memory Utilization</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/default.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
        <script>hljs.highlightAll();</script>
    </head>
    <body>
        <br>
        <div class="container">
            <div class="row">
                <div class="card-group">
                    {fragments}
                </div>
            </div>
            <div class="row mt-4">
                <div class="col">
                    <p class="lead">
                        A Python generator is a special type of iterator that allows you to iterate over
                        a sequence of values. Unlike lists, generators do not store all the values in memory;
                        instead, they generate values on the fly and yield them one at a time. This makes generators
                        more memory-efficient, especially for large datasets.
                    </p>
                    <h3>Key Differences:</h3>

                    <ol>
                        <li><b>Memory Usage</b>:
                            <ul>
                                <li><b>List</b>: Stores all elements in memory.</li>
                                <li><b>Generator</b>: Generates elements on the fly and does not store them in memory.</li>
                            </ul>
                        </li>
                        <li><b>Syntax</b>:
                            <ul>
                                <li><b>List</b>: Created using square brackets <code>[]</code>.</li>
                                <li><b>Generator</b>: Created using parentheses <code>()</code> or by using a function with the <code>yield</code> keyword.</li>
                            </ul>
                        </li>
                        <li><b>Evaluation</b>:
                            <ul>
                                <li><b>List</b>: Evaluated immediately and all elements are stored in memory.</li>
                                <li><b>Generator</b>: Evaluated lazily, meaning elements are generated only when requested.</li>
                            </ul>
                        </li>
                        <li><b>Performance</b>:
                            <ul>
                                <li><b>List</b>: Faster for accessing elements multiple times since they are stored in memory.</li>
                                <li><b>Generator</b>: More efficient for large datasets or streams of data where you only need to iterate once.</li>
                            </ul>
                        </li>
                    </ol>

                    <h3>Examples</h3>

                    <h4>List:</h4>
<pre><code class="language-python"># List comprehension
squares_list = [x * x for x in range(10)]
print(squares_list)
</code></pre>

                    <h4>Generator:</h4>
<pre><code class="language-python"># Generator expression
squares_generator = (x * x for x in range(10))
print(list(squares_generator))  # Convert to list to print all values
</code></pre>

                    <h4>Generator Function:</h4>
<pre><code class="language-python">def squares_gen(n):
    for x in range(n):
        yield x * x

gen = squares_gen(10)
print(list(gen))  # Convert to list to print all values
</code></pre>

                    <p>
                        In summary, use a list when you need to store and access elements multiple times,
                        and use a generator when you need to iterate over a large dataset or stream of data efficiently.
                    </p>
                </div>
            </div>
        </div>
    </body>
</html>
"""

# DIVIDER = '<div class="divider divider-horizontal"></div>'
DIVIDER = ""

CODE_FRAGMENT = """
                    <div class="card">
                        <div class="card-header font-monospace">{header}</div>
                        <div class="card-body">
                            <pre><code class="language-python">{code}</code></pre>
                            <br>
                        </div>
                    </div>
"""


def get_interfaces_generator():
    data = requests.get(
        f"{TEST_API_URL}/api/dcim/devices",
        headers=TEST_API_HEADERS,
        params={"limit": 200},
        timeout=60,
    ).json()
    yield from data["results"]
    while data["next"]:
        data = requests.get(
            data["next"], headers=TEST_API_HEADERS, params={"limit": 200}, timeout=60
        ).json()
        yield from data["results"]


def get_interfaces_list():
    data = requests.get(
        f"{TEST_API_URL}/api/dcim/devices",
        headers=TEST_API_HEADERS,
        params={"limit": 200},
        timeout=60,
    ).json()
    result_data = data["results"]
    while data["next"]:
        data = requests.get(
            data["next"], headers=TEST_API_HEADERS, params={"limit": 200}, timeout=60
        ).json()
        result_data.extend(data["results"])
    return result_data


def get_peak_memory(func):
    tracemalloc.start()
    counter = 0
    for _ in func():
        counter += 1
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak, counter


def format_size(size):
    """Format a size in bytes to a human-readable string. Borrowed from stdlib tracemalloc."""
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(size) < 100 and unit != "B":
            # 3 digits (xx.x UNIT)
            return "%.1f %s" % (size, unit)  # pylint: disable=consider-using-f-string
        if abs(size) < 10 * 1024 or unit == "TiB":
            # 4 or 5 digits (xxxx UNIT)
            return "%.0f %s" % (size, unit)  # pylint: disable=consider-using-f-string
        size /= 1024


def build_fragment(func):
    start_time = time.time()
    peak, counter = get_peak_memory(func)
    end_time = time.time()
    code = inspect.getsource(func)
    code = html.escape(code)
    code = (
        f"# Ram used (peak): {format_size(peak)}\n"
        f"# Elapsed time: {round(end_time - start_time, 2)} seconds\n"
        f"# Number of items processed: {counter}\n\n" + code
    )
    return CODE_FRAGMENT.format(code=code, header=func.__name__)


def generate_html():
    fragments = [
        build_fragment(get_interfaces_generator),
        build_fragment(get_interfaces_list),
    ]
    fragments = DIVIDER.join(fragments)
    return HTML_BODY.format(fragments=fragments)


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(generate_html().encode())


def main():
    with http.server.HTTPServer(("localhost", 8000), RequestHandler) as httpd:
        print("Serving HTTP on localhost port 8000 (http://localhost:8000/) ...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
            exit(0)


if __name__ == "__main__":
    main()
