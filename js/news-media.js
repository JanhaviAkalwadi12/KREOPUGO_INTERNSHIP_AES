document.addEventListener('DOMContentLoaded',function(){
  if(window.jQuery&&jQuery.fn.magnificPopup){jQuery('.image-popup').magnificPopup({type:'image',gallery:{enabled:true}});}
  document.querySelectorAll('[data-video-slider]').forEach(function(slider){
    const track=slider.querySelector('.nm-video-track'), cards=[...slider.querySelectorAll('.nm-video-card')], prev=slider.querySelector('[data-prev]'), next=slider.querySelector('[data-next]');
    const image=slider.querySelector('[data-feature-image]'), title=slider.querySelector('[data-feature-title]'), desc=slider.querySelector('[data-feature-description]'), number=slider.querySelector('[data-feature-number]');
    if(!track||!cards.length)return; let index=0;
    function visible(){return window.innerWidth<768?1:(window.innerWidth<992?2:4)}
    function select(i){index=Math.max(0,Math.min(i,cards.length-1)); const c=cards[index]; cards.forEach(x=>x.classList.toggle('is-selected',x===c)); if(image) image.src=c.dataset.videoImage; if(title) title.innerHTML=c.dataset.videoTitle; if(desc) desc.textContent=c.dataset.videoDescription; if(number) number.textContent=String(index+1).padStart(2,'0'); const dots=slider.querySelectorAll('.nm-video-dots span'); dots.forEach((d,j)=>d.classList.toggle('active',j===index)); const v=visible(), max=Math.max(0,cards.length-v), left=Math.min(index,max), gap=14, w=cards[0].getBoundingClientRect().width+gap; track.style.transform='translateX('+(-left*w)+'px)'; }
    cards.forEach((c,i)=>c.addEventListener('click',function(){select(i)}));
    prev&&prev.addEventListener('click',function(){select(index-1)}); next&&next.addEventListener('click',function(){select(index+1)}); window.addEventListener('resize',function(){select(index)}); select(0);
  });
});
