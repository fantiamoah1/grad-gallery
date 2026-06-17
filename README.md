# Grad Gallery

Grad Gallery is a graduation portrait booking marketplace MVP.

Students can:

- View packages
- Browse photographers
- Submit a booking request

Admin can:

- View booking requests
- Update booking status
- Track payment status
- Track gallery delivery status
- Assign photographers
- Export bookings as CSV

## Public Hosting On Render

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
python outputs/grad_gallery_booking_server.py
```

Set this environment variable in Render:

```text
GRAD_GALLERY_ADMIN_PASSWORD=your-private-password
```

## Local Run

```bash
python outputs/grad_gallery_booking_server.py
```

Then open:

```text
http://127.0.0.1:8765
```

## Important

This MVP uses SQLite. For demos and early testing, this is fine. Before taking real paid bookings, upgrade storage to Google Sheets, Supabase/Postgres, or a Render persistent disk.
