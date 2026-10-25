"""Manual moderation CLI. Run inside API container, never expose as a web endpoint.

Examples:
 python scripts/photo_moderation_admin.py list
 python scripts/photo_moderation_admin.py hide <32-character-photo-name> --reason '...'
 python scripts/photo_moderation_admin.py unhide <32-character-photo-name> --reason 'appeal accepted'
"""
import argparse
from sqlalchemy import text
from backend.app.core.database import SessionLocal
from backend.app.modules.media.security import IDENT


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=('list', 'hide', 'unhide'))
    p.add_argument('photo_name', nargs='?')
    p.add_argument('--reason', default='')
    args = p.parse_args()
    with SessionLocal() as db:
        if args.action == 'list':
            rows = db.execute(text('''SELECT photo_name, reason, count(*) AS reports,
                min(created_at) AS first_report FROM photo_reports
                WHERE status='open' GROUP BY photo_name, reason ORDER BY reports DESC, first_report ASC LIMIT 100'''))
            for row in rows:
                print(row.photo_name, row.reason, row.reports, row.first_report)
            return
        if not args.photo_name or not IDENT.fullmatch(args.photo_name):
            p.error('hide/unhide requires a 32-character hex photo_name')
        if not args.reason.strip() or len(args.reason.strip()) > 500:
            p.error('--reason is required (up to 500 chars)')
        # Reversible restriction; report history stays audit-accessible.
        hidden = args.action == 'hide'
        db.execute(text('''INSERT INTO photo_moderation(photo_name, hidden, reason, updated_at)
            VALUES (:name, :hidden, :reason, now())
            ON CONFLICT(photo_name) DO UPDATE SET hidden=excluded.hidden,
                reason=excluded.reason, updated_at=now()'''),
            {'name': args.photo_name, 'hidden': hidden, 'reason': args.reason.strip()})
        db.execute(text('''UPDATE photo_reports SET status='reviewed' WHERE photo_name=:name'''), {'name': args.photo_name})
        db.commit()
        print('hidden' if hidden else 'visible', args.photo_name)

if __name__ == '__main__':
    main()
