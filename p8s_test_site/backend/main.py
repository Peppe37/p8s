"""
p8s_test_site - A P8s Application
"""

from p8s import P8sApp

app = P8sApp(title="p8s_test_site")


@app.get("/")
async def root():
    return {"message": "Welcome to p8s_test_site! 🔥"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
