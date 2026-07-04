#include <fcntl.h>
#include <unistd.h>
#include <seccomp.h>
#include <stdio.h>

int main(int argc, char **argv)
{
    if (argc != 2) {
        printf("!!!! Need ID number as second argument\n");
        return 1;
    }

    /// Open the output files FIRST -- this happens BEFORE the filter is
    /// loaded, so comp3's own openat calls are allowed. The descriptors
    /// stay open across execve (open() does not set close-on-exec), so
    /// app3 inherits them.
    int fd0 = open("output0.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    int fd1 = open("output1.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);

    /// Setup seccomp filter:
    ///   default: ALLOW every syscall
    ///   audit write and clone (the same syscalls logged in Task 7)
    ///   BLOCK openat so the launched app cannot open any files
    scmp_filter_ctx ctx;
    ctx = seccomp_init(SCMP_ACT_ALLOW);
    seccomp_rule_add(ctx, SCMP_ACT_LOG,  SCMP_SYS(write),  0);
    seccomp_rule_add(ctx, SCMP_ACT_LOG,  SCMP_SYS(clone),  0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(openat), 0);
    seccomp_load(ctx);   // filter goes live here; inherited across execve

    /// Pass the two fd numbers to app3 as extra command-line arguments
    char fd0_str[12], fd1_str[12];
    sprintf(fd0_str, "%d", fd0);
    sprintf(fd1_str, "%d", fd1);

    /// Launch app3: argv = { "./app3", <ID>, <fd0>, <fd1>, NULL }
    char *args[] = {"./app3", argv[1], fd0_str, fd1_str, NULL};
    execve(args[0], args, NULL);

    perror("execve failed");
    return 1;
}