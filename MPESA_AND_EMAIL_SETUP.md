# Email, SMS (registration), and M-Pesa Daraja (STK)

## 1. Customer registration email

Set SMTP (example for Gmail app password or your provider):

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-shop@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-shop@gmail.com
```

With `DEBUG=True`, the default backend prints emails to the console if you omit the above.

## 2. SMS after registration (phone)

Daraja does not provide a simple “welcome SMS” in the same way as STK. For **SMS to the registered phone**, this project uses **optional Africa’s Talking**:

```env
REGISTRATION_SMS_ENABLED=true
AT_USERNAME=sandbox
AT_API_KEY=your_api_key
```

If disabled or not configured, registration still succeeds; only email (if SMTP is set) is sent.

## 3. M-Pesa Daraja — Lipa na M-Pesa Online (M-Pesa Express / STK)

This is the **merchant-initiated** flow: your server calls Daraja, and the customer gets the **Enter PIN** prompt on their phone.

**HTTP endpoints (STK `processrequest`):**

| Environment | URL |
|-------------|-----|
| Sandbox | `https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest` |
| Production | `https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest` |

OAuth token (same host): `GET .../oauth/v1/generate?grant_type=client_credentials` with **Basic** auth `(consumer_key:consumer_secret)`.

### Sandbox test credentials (from Daraja portal)

Typical **Lipa na M-Pesa Online / Simulate** values:

- **Business ShortCode:** `174379`
- **Passkey:** (copy from portal — long hex string)
- **Test MSISDN:** `254708374149` (use as the phone you enter in the payment form)

**Note:** *Initiator name / password* in the portal apply to **other** APIs (e.g. B2C), **not** to STK Push. For STK you only need consumer key/secret, shortcode, passkey, and callback URL.

### Callback URL

Must be **public HTTPS** (ngrok / your deployed domain). Our app expects:

`https://YOUR_DOMAIN/customers/mpesa/stk-callback/`

### Environment variables

```env
MPESA_DARAJA_ENABLED=true
MPESA_ENV=sandbox
MPESA_CONSUMER_KEY=...
MPESA_CONSUMER_SECRET=...
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey_from_portal
MPESA_CALLBACK_URL=https://YOUR_DOMAIN/customers/mpesa/stk-callback/
# Paybill: CustomerPayBillOnline (default). Till / Buy Goods: CustomerBuyGoodsOnline
MPESA_TRANSACTION_TYPE=CustomerPayBillOnline
# Usually same as shortcode for paybill; set only if PartyB differs (till scenarios)
# MPESA_PARTY_B=174379
```

**Production:** set `MPESA_ENV=production`, use **live** shortcode/passkey from your approved app, and a live callback URL.

Our code sends the same **JSON field types** as Daraja’s samples (e.g. `Amount`, `BusinessShortCode`, and phone fields as **strings**).

Customers see **“Pay with M-Pesa (STK)”** on the M-Pesa payment page when `MPESA_DARAJA_ENABLED=true`. Manual entry (amount + confirmation code) remains as a fallback.
