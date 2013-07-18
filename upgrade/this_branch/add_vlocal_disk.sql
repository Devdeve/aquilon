-- DISK

ALTER TABLE disk ADD filesystem_id INTEGER;
ALTER TABLE disk ADD CONSTRAINT disk_filesystem_fk FOREIGN KEY (filesystem_id) REFERENCES filesystem (id) ON DELETE CASCADE;

CREATE INDEX disk_filesystem_idx ON disk (filesystem_id);

QUIT;
