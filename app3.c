#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define ID_SIZE 8
#define BUF_SIZE 100

int main(int argc, char **argv)
{
    pid_t pid;
    int i;
    char buf[BUF_SIZE];

    /// app3 is NOT allowed to open files. Instead, comp3 opens them and
    /// passes the file descriptors in as command-line arguments:
    ///   argv[1] = ID, argv[2] = fd for output0.txt, argv[3] = fd for output1.txt
    int fds[2];
    fds[0] = atoi(argv[2]);   // output0.txt
    fds[1] = atoi(argv[3]);   // output1.txt

    /// parse the input ID
    char id[ID_SIZE];
    int upper_limit = ID_SIZE;
    if (strlen(argv[1]) < ID_SIZE) {
        memcpy(id, argv[1], strlen(argv[1]));
        upper_limit = (int)strlen(argv[1]);
    } else {
        memcpy(id, argv[1], ID_SIZE);
    }

    /// fork and get the pid after forking
    fork();
    pid = getpid();

    /// iterate over ID writing digits to the output files (via inherited fds)
    for (i = 0; i < upper_limit; i++) {
        int digit = id[i]-0x30;         // convert ascii of int to int
        if (pid%2 == digit%2) {
            sprintf(buf, "(pid=%d) (i=%d) value = %d\n", pid, i, digit);
            write(fds[pid%2], buf, strlen(buf));
        }
    }

    close(fds[0]);
    close(fds[1]);
    return 0;
}