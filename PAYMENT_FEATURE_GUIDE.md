# Payment Feature Implementation Guide

## Overview
A comprehensive payment feature has been implemented in the car detailing workflow management system that allows customers to choose between M-Pesa (automatic) and Cash payment methods, with proper status tracking and authorization rules.

## Key Features Implemented

### 1. **Customer Payment Method Selection**
**Location:** After booking a new job

**User Flow:**
1. Customer books a job with services
2. Redirected to `job_select_payment_method` page
3. Customer chooses:
   - **M-Pesa**: Automatic payment with immediate status update
   - **Cash**: Manual recording by manager

**Files Modified:**
- `apps/customers/forms.py` - Added `PaymentMethodSelectionForm`
- `apps/customers/views.py` - Added `customer_job_select_payment_method_view`
- `apps/customers/urls.py` - Added payment method selection URL
- `templates/customers/job_select_payment_method.html` - New template

### 2. **Payment Channel Tracking**
**Job Model Fields:**
```python
payment_channel = 'unspecified', 'mpesa', or 'cash'
payment_status = 'pending', 'partial', 'paid', 'refunded'
amount_paid = Decimal amount
mpesa_phone / mpesa_transaction_id = Transaction details
```

### 3. **M-Pesa Payment Flow**
**Automatic Payment Processing:**
- Customer pays via M-Pesa from customer portal
- System immediately updates `amount_paid` and `payment_status`
- Transitions to `'paid'` when balance >= total_price
- Timeline event recorded automatically

**Method:** `Job.apply_mpesa_payment(amount, phone, transaction_id, user)`

### 4. **Cash Payment Flow (Manager Recording)**
**Manager-Controlled Recording:**
- Customer selects Cash at payment method selection
- Manager records payment in Job Edit form
- Form: `CashPaymentRecordingForm` (newly added)
- Updates payment status and timeline
- Payment immediately reflected in system

**Method:** `Job.apply_cash_payment(amount, payment_status, user, notes)`

### 5. **Job Status Completion Logic**
**Critical Rules:**
- Job can ONLY be marked "Completed" when ALL services are marked as done
- If any service is pending, completion is blocked
- Payment completion does NOT gate job status completion
- Status progression:
  - WAITING → IN_PROGRESS
  - IN_PROGRESS → AWAITING_EXTRA (when extra services added)
  - AWAITING_EXTRA → IN_PROGRESS (back to work)
  - IN_PROGRESS → COMPLETED (only if all services done)
  - Any → CANCELLED

**Helper Methods Added:**
- `Job.can_be_completed()` - Check if completion is allowed
- `Job.get_completion_blockers()` - Return list of reasons why job can't be completed
- `Job.has_pending_services()` - Check if services are incomplete

### 6. **Role-Based Payment Visibility**

#### **Customer View**
- Sees total price, amount paid, balance due
- Payment status badge
- Conditional actions:
  - If M-Pesa: "Pay KES XXX with M-Pesa" button
  - If Cash: "Bring KES XXX when you visit" message
  - If Not Set: "Choose payment method" button

#### **Worker View**
- Sees payment status (Pending, Partial, Paid)
- Alert: "Check payment before releasing vehicle"
- Cannot modify payment information
- Only manager can update cash payments

#### **Manager View**
- Full edit access to payment fields
- Can update payment channel, status, amount
- Form for recording cash payments
- Timeline shows all payment changes
- Alert for outstanding cash payments

### 7. **Payment Status Display**

**Badge Colors:**
- 🟢 **Paid**: Green badge
- 🟡 **Partially Paid**: Yellow badge
- ⚫ **Pending**: Gray badge

**Timeline Events:**
- All payments logged in job timeline
- Type: `'payment_mpesa'` or `'payment_cash'`
- Includes amount, balance, transaction details
- User and timestamp tracked

## Database Considerations

No migration required - all fields already exist in Job model:
- `payment_status`
- `payment_channel`
- `amount_paid`
- `mpesa_phone`
- `mpesa_transaction_id`
- `timeline` (JSON field)

## Forms Added/Modified

### New Forms:
1. **PaymentMethodSelectionForm** (`apps/customers/forms.py`)
   - Radio select: M-Pesa or Cash
   - Help text explaining each option

2. **CashPaymentRecordingForm** (`apps/jobs/forms.py`)
   - Amount field (max = balance due)
   - Payment status selector (Partial/Paid)
   - Notes field for manager comments

### Existing Forms Modified:
- **JobEditForm** - Already had payment fields, no changes needed

## Templates Created/Modified

### New Templates:
1. **`templates/customers/job_select_payment_method.html`**
   - Payment method selection page
   - M-Pesa vs Cash comparison
   - Job summary display
   - FAQ section explaining the choices

### Modified Templates:
1. **`templates/jobs/job_detail.html`**
   - Enhanced payment section with:
     - Payment channel display with icon
     - Payment amount summary cards
     - Role-based payment guidance
     - Action buttons based on role and status
   - Improved service completion messaging

2. **`templates/customers/portal.html`**
   - Updated payment method buttons
   - Shows "Pay M-Pesa" or "Choose method" based on selection

## Views Updated

### New Views:
1. **`customer_job_select_payment_method_view`** (`apps/customers/views.py`)
   - Handles payment method selection
   - Sets payment_channel on job
   - Redirects to M-Pesa form or job detail

### View Logic:
- Booking flow: Book Job → Select Payment Method → (M-Pesa or Done)
- Payment updates trigger timeline events
- Manager edit view logs payment changes

## URL Routes Added

```python
# Customer portal payment method selection
path('portal/jobs/<int:job_pk>/payment-method/',
     views.customer_job_select_payment_method_view,
     name='job_select_payment_method')
```

## Key Business Rules

### Payment Method:
1. Customers choose method at job booking
2. Can be changed by manager anytime before completion
3. M-Pesa: Automatic updates from customer portal
4. Cash: Manager must manually record receipt

### Job Completion:
1. **Service Completion MUST happen before Status Completion**
   - Worker marks each service as done
   - System tracks completion timestamp and responsible user
2. **All Services Must Be Done**
   - Cannot mark job completed if any service pending
   - Clear error messages guide users
3. **Payment Does NOT Block Completion**
   - Job can be completed even if payment incomplete
   - Payment tracking is independent of job status

### Status Transitions:
- **Waiting** → In Progress / Cancelled
- **In Progress** → Awaiting Extra / Completed / Cancelled
- **Awaiting Extra** → In Progress / Completed
- **Completed** → (No transitions)
- **Cancelled** → (No transitions)

## Timeline Event Types

### Payment Events:
```
event_type='payment_mpesa'
event_type='payment_cash'
Description: "M-Pesa payment recorded: KES 5000 (balance KES 2000)"
```

### Status Events:
```
event_type='status_change'
Description: "Status changed from in_progress to completed"
```

## Testing Checklist

- [ ] Customer books job → Select payment method shown
- [ ] M-Pesa selected → Redirects to M-Pesa payment form
- [ ] Cash selected → Redirects to job detail
- [ ] M-Pesa payment → Amount updates immediately
- [ ] Worker sees payment status on job detail
- [ ] Manager can edit payment for cash jobs
- [ ] Service completion required before job completion
- [ ] Job status shows correct blockers if can't complete
- [ ] Timeline shows all payment changes
- [ ] Customer portal shows payment method buttons correctly
- [ ] Payment badges display correct colors

## Security Considerations

1. **Customer Portal**: Only M-Pesa payments (automatic)
2. **Manager Only**: Cash payment recording in Job Edit
3. **Workers**: View-only access to payment status
4. **Timeline**: All changes attributed to user with timestamp
5. **Permissions**: Decorator checks ensure role-based access

## Future Enhancements

1. **M-Pesa Integration**: Connect to M-Pesa API for real payment processing
2. **Payment Receipts**: Generate PDF/email receipts for customers
3. **Refunds**: Implement refund processing for overpayments
4. **Partial Payments**: Better UI for payment plans
5. **Recurring Customers**: Save preferred payment method
6. **Payment Analytics**: Reports on payment patterns and on-time rates
7. **Automated Reminders**: SMS/Email for outstanding payments
8. **Online Portal for Managers**: Dedicated payment management dashboard
