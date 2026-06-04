# Django View API Practice

**Name:** Syed Abdullah Al Muyeed  
**ID:** FT0061-I  
**Designation:** Information Technology Intern

---

# Django Class-Based Views

## ListView

Displays a list of model objects and automatically handles queryset management, pagination, and context generation.

<img src="screenshots/task0_listview.png" width="800">

## CreateView

Provides a form for creating new records. Handles form validation, object creation, and redirection after successful submission.

<img src="screenshots/task0_createview.png" width="800">

## UpdateView

Allows editing existing records. The form is automatically populated with existing data.

<img src="screenshots/task0_updateview.png" width="800">

## DeleteView

Shows a confirmation page before deletion. A GET request displays the confirmation page and a POST request performs the deletion.

<img src="screenshots/task0_deleteview.png" width="800">

---

# Account API

## GET /api/accounts/

Returns all available accounts.

Status Code: **200 OK**

<img src="screenshots/api_accounts_list.png" width="800">

## POST /api/accounts/

Creates a new account.

Status Code: **201 Created**

<img src="screenshots/api_accounts_create.png" width="800">

## GET /api/accounts/{id}/

Returns details of a specific account, including the associated user email.

Status Code: **200 OK**

<img src="screenshots/api_accounts_detail.png" width="800">

## PUT /api/accounts/{id}/

Performs a full update of an account.

Status Code: **200 OK**

<img src="screenshots/api_accounts_update.png" width="800">

## PATCH /api/accounts/{id}/

Performs a partial update of an account.

Status Code: **200 OK**

<img src="screenshots/api_accounts_partial_update.png" width="800">

## DELETE /api/accounts/{id}/

Deletes an account.

Status Code: **204 No Content**

<img src="screenshots/api_accounts_delete.png" width="800">

---

# Transaction API

## GET /api/transactions/

Returns all transactions.

Status Code: **200 OK**

<img src="screenshots/api_transactions_list.png" width="800">

## POST /api/transactions/

Creates a new transaction.

Status Code: **201 Created**

<img src="screenshots/api_transactions_create.png" width="800">

## GET /api/transactions/{id}/

Returns details of a specific transaction.

Status Code: **200 OK**

<img src="screenshots/api_transactions_detail.png" width="800">

## PUT /api/transactions/{id}/

Performs a full update of a transaction.

Status Code: **200 OK**

<img src="screenshots/api_transactions_update.png" width="800">

## PATCH /api/transactions/{id}/

Performs a partial update of a transaction.

Status Code: **200 OK**

<img src="screenshots/api_transactions_partial_update.png" width="800">

## DELETE /api/transactions/{id}/

Deletes a transaction.

Status Code: **204 No Content**

<img src="screenshots/api_transactions_delete.png" width="800">

---

# Custom Actions

## Freeze Account

Endpoint:

`POST /api/accounts/{id}/freeze/`

Returns:

`{"status": "frozen"}`

or

`{"status": "unfrozen"}`

<img src="screenshots/api_accounts_freeze.png" width="800">

## Account Statement

Endpoint:

`GET /api/accounts/{id}/statement/`

Returns account information together with all related transactions.

<img src="screenshots/api_accounts_statement.png" width="800">

## Reverse Transaction

Endpoint:

`POST /api/transactions/{id}/reverse/`

Returns:

`{"status": "reversed"}`

<img src="screenshots/api_transactions_reverse.png" width="800">

## Duplicate Reverse Request

If a transaction has already been reversed, the endpoint returns:

`400 Bad Request`

`{"error": "Already reversed"}`

<img src="screenshots/api_transactions_reverse_duplicate.png" width="800">

---

# Overriding get_queryset

```python
def get_queryset(self):
    if not self.request.user.is_authenticated:
        return Account.objects.none()
    return Account.objects.filter(user=self.request.user)
```

Anonymous users receive an empty response because they do not own any accounts.

<img src="screenshots/api_accounts_anonymous.png" width="800">

Authenticated users only receive accounts associated with their own profile.

<img src="screenshots/api_accounts_logged_in.png" width="800">

---

# Overriding get_serializer_class

```python
def get_serializer_class(self):
    if self.action == "retrieve":
        return AccountDetailSerializer
    return AccountSerializer
```

The list endpoint uses the standard serializer.

<img src="screenshots/api_accounts_list.png" width="800">

The detail endpoint uses a specialized serializer that includes the `user_email` field.

<img src="screenshots/api_accounts_detail.png" width="800">
