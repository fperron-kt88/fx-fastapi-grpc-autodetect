# grpc to fastapi intergration - exchanging data with an esp32


### Certificate installation

Generate the certificates with these commands:

```bash
mkdir -p certs
openssl genrsa -out ./certs/acme.key 2048
openssl req -new -x509 -key ./certs/acme.key -out certs/acme.crt -days 365 -subj "/C=US/ST=Acme/L=SelfSigned/O=AcmeTesting/OU=IT/CN=localhost"
```