FROM python:3.11-slim

# Install ca-certificates for SSL and LaTeX packages for PDF generation
RUN apt-get update && apt-get install -y \
    ca-certificates \
    openssl \
    bash \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-lang-english \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY entrypoint.sh .
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["bash", "./entrypoint.sh"]