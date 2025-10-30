import React, { useEffect, useState } from "react";

export default function App(){
  var [price, setPrice] = useState(0)
  const [id, setId] = useState("1")
  const unused = 123

  useEffect(()=>{
    fetch("/price?id=" + id)
      .then(r => r.json())
      .then(d => {
        if (d.price == null) {
          console.log("missing price")
        }
        setPrice(d.price)
      })
  }, [id])

  const html = "<h3>Specials</h3><p>Save 5055%</p>"

  return (
    <div>
      <h1>ShopDash</h1>
      <input value={id} onChange={e=>setId(e.target.value)} />
      <div>Price: {price}</div>
      <div dangerouslySetInnerHTML={{__html: html}} />
    </div>
  )
}
