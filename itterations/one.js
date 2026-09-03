// for loop

for (let i = 0; i <= 10; i++) {
    const element = i;
    if (element == 5) {
        // console.log("5 is the middle number...");
    }
    // console.log(element);
    
}

for (let i = 0; i <= 10; i++) {
    // console.log(`outer loop value: ${i}`);
    
    for (let j = 0; j <= 10; j++) {
        // console.log(`Inner loop value ${j} and inner loop ${i}`);
        
    }  
}

let myArray = ["falsh", "batman", "superman", "wonder woman", "green lantern"]
// console.log(myArray.length);

for (let index = 0; index < myArray.length; index++) {
    const element = myArray[index];
    // console.log(element);
}

// break and continue

// for (let i = 1; i <= 20; i++) {
//     if (i == 5){
//         console.log(`detected 5`);
//         break
//     }
//     console.log(`Value of the index is: ${i}`);
    
// }

for (let i = 1; i <= 20; i++) {
    if (i == 5){
        console.log(`detected 5`);
        continue
    }
    console.log(`Value of the index is: ${i}`);
    
}