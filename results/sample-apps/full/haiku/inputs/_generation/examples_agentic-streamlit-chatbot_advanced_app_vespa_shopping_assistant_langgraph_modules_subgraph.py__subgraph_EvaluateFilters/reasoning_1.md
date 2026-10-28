The function calls ChatOpenAI — a network call to OpenAI. That cannot run here. The core of the function is an LLM invocation. So we must reply CANNOT RUN.

Indeed: `model = ChatOpenAI(...)`, `chain.invoke(...)` — requires network/credentials. So CANNOT RUN.