# reader_to_pinboard
Simple script for sending archived Readwise Reader items to Pinboard. Need to
mount a state file:

```
/usr/local/bin/docker run --rm --volume ~/.r2pstate.txt:/state.txt python-r2p
```
