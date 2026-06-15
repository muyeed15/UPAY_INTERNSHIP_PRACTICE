# DRF Serializer Practice

**Name:** Syed Abdullah Al Muyeed  
**ID:** FT0061-I  
**Designation:** Information Technology Intern

---

## Serializers

| Serializer | Type | Purpose |
|---|---|---|
| `AccountBaseSerializer` | `Serializer` | Manual fields, custom create/update, validators |
| `AccountSerializer` | `ModelSerializer` | Auto-generated from Account model |
| `AccountDetailSerializer` | `ModelSerializer` + source | Adds `user_email` from related User |
| `AccountBulkSerializer` | `ModelSerializer` + `ListSerializer` | Bulk create with `list_serializer_class` |
| `TransactionSerializer` | `ModelSerializer` | Flat transaction fields |
| `TransactionDetailSerializer` | `ModelSerializer` (nested) | Embeds `AccountDetailSerializer` with user_email |
| `TransactionNestedWriteSerializer` | `Serializer` (nested write) | Creates Transaction + Account in one call |
| `AccountStatementSerializer` | `ModelSerializer` + `SerializerMethodField` | Computed fields: transaction_count, totals, balance_in_taka, last_active |
| `AccountOverrideSerializer` | `ModelSerializer` + `to_representation` | Custom I/O transforms, adds `status` and `balance_formatted` |

## Custom Fields

- **`MoneyField`** - Stores USD, displays BDT at 1 USD = 110 BDT. `to_representation` / `to_internal_value` conversion.
- **`MaskedCardField`** - Displays `**** **** **** 1234`, stores full 16-digit number.

## API

### Accounts (`/api/accounts/`)
| Method | Endpoint | Serializer |
|---|---|---|
| GET/POST | `/api/accounts/` | `AccountSerializer` |
| GET | `/api/accounts/{id}/` | `AccountDetailSerializer` |
| PUT/PATCH/DELETE | `/api/accounts/{id}/` | `AccountSerializer` |
| POST | `/api/accounts/{id}/freeze/` | Toggle freeze |
| GET | `/api/accounts/{id}/statement/` | `AccountStatementSerializer` |

### Transactions (`/api/transactions/`)
| Method | Endpoint | Serializer |
|---|---|---|
| GET/POST | `/api/transactions/` | `TransactionSerializer` |
| GET | `/api/transactions/{id}/` | `TransactionDetailSerializer` |
| PUT/PATCH/DELETE | `/api/transactions/{id}/` | `TransactionSerializer` |
| POST | `/api/transactions/{id}/reverse/` | Reverse transaction |

### Batch
| Method | Endpoint | Serializer |
|---|---|---|
| POST | `/api/accounts/bulk/` | `AccountBulkSerializer` with `many=True` |

### Auth
| Endpoint | Description |
|---|---|
| `/api/token/` | Obtain JWT pair |
| `/api/token/refresh/` | Refresh JWT |

## Tests

```bash
python manage.py test accounts.tests -v 2
```
