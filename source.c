/*
 * File: source.c
 * Author: Thierry Seegers
 * License: Public Domain
 */

#include <stdio.h> // For printf

// Prints on screen double the value of the given argument.
void print_double(int const i)
{
    printf("%d\n", i * 2);
}

int main()
{
	/* Calls the print_double function with 22, 33 and 44 as arguments. */
    print_double(22);
    print_double(33);
    print_double(44);

    /* // Pathological case 1 */

    /* // Pathological case 2
     */

    // /* Pathological case 3

    print_double(55);	/* Pathological case 4
    // */

    // Pa-	// tho- // lo-	// gical case 5

    /* Pa- */ print_double(66); /* tho- */	/* lo- *//* gical case 6 */

    /* Patho- 
        */  /* lo-
               gical case 7 */

    // Multiple \
	   lines   \
       case 1

    /* Multiple lines \
       case 2
	*/

    return 0;
}